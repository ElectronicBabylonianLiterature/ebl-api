import json
from urllib.parse import unquote
from typing import Optional, cast

import falcon

from ebl.errors import DataError, Defect
from ebl.common.domain.scopes import Scope
from ebl.media.application.media_management import (
    MediaConflictError,
    MediaPermissionError,
)
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.web.dtos import parse_museum_number
from ebl.media.application.media_dtos import FragmentMediaResponseDto
from ebl.media.application.media_errors import (
    MediaNotFoundError,
    MediaRepresentationNotFoundError,
)
from ebl.media.application.media_runtime import MediaRuntime
from ebl.media.application.media_schemas import FragmentMediaResponseDtoSchema
from ebl.media.application.media_storage_identity import StoredRepresentationHandle
from ebl.media.application.media_stored import StoredMedia
from ebl.media.domain import MediaId, ThumbnailSize
from ebl.media.domain.mime import is_svg_mime_type
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.users.domain.user import User


def _private_response(response: falcon.Response) -> None:
    response.set_header("Cache-Control", "private, no-store")
    response.set_header("Vary", "Authorization")
    response.set_header("X-Content-Type-Options", "nosniff")


def _media_id(value: str) -> MediaId:
    try:
        return MediaId(value)
    except ValueError as error:
        raise DataError("Invalid media identifier.") from error


def _representation_handle(
    stored: StoredMedia, representation: str, size: Optional[str]
) -> StoredRepresentationHandle:
    if representation == "file":
        return stored.representations.original
    if representation == "display":
        handle = stored.representations.display
    else:
        try:
            thumbnail_size = ThumbnailSize(size)
        except ValueError as error:
            raise DataError("Invalid thumbnail size.") from error
        handle = stored.representations.thumbnail(thumbnail_size)
    if handle is None:
        raise MediaRepresentationNotFoundError(stored.media.id, representation)
    return handle


class MediaResource:
    def __init__(self, fragments: FragmentRepository, runtime: MediaRuntime) -> None:
        self._fragments = fragments
        self._runtime = runtime

    @staticmethod
    def _permissions(req):
        user = cast(User, req.context["user"])
        return (
            user.subject,
            user.has_scope(Scope.MANAGE_FRAGMENT_MEDIA),
            user.has_scope(Scope.UPLOAD_FRAGMENT_MEDIA),
        )

    def _management(self):
        if self._runtime.management is None:
            raise falcon.HTTPNotFound()
        return self._runtime.management

    def _writer(self, req, *, manager_only=False):
        management = self._management()
        actor, manager, contributor = self._permissions(req)
        if (
            not isinstance(actor, str)
            or not actor.strip()
            or not (manager or (contributor and not manager_only))
        ):
            raise falcon.HTTPForbidden()
        return management, actor, manager, contributor

    @staticmethod
    def _response(number, media, *, management=False):
        result = FragmentMediaResponseDtoSchema().dump(
            FragmentMediaResponseDto.of(number, media)
        )
        for resource, item in zip(result["media"], media, strict=True):
            if item.submission is not None:
                submission = item.submission
                resource.update(
                    publicationStatus=submission.publication_status.value,
                    creator=submission.creator,
                    sourceInstitution=submission.source_institution,
                    copyrightHolder=submission.copyright_holder,
                    rightsStatement=submission.rights_statement,
                )
                if management:
                    resource.update(
                        originalFilename=item.original_filename,
                        uploaderId=submission.uploader_id,
                        uploadedAt=submission.uploaded_at,
                        permissionAttested=submission.permission_attested,
                        description=submission.description,
                        projects=[project.name for project in item.projects],
                        reviewerId=submission.reviewer_id,
                        reviewedAt=submission.reviewed_at,
                        reviewReason=submission.review_reason,
                    )
            elif item.rights is not None:
                resource.update(
                    rightsAnnotated=True,
                    creator=item.rights.creator,
                    sourceInstitution=item.rights.source_institution,
                    copyrightHolder=item.rights.copyright_holder,
                    rightsStatement=item.rights.rights_statement,
                    description=item.rights.description,
                )
        return result

    @staticmethod
    def _json_body(req):
        if req.content_length is not None and req.content_length > 16384:
            raise falcon.HTTPPayloadTooLarge(
                description="Media metadata exceeds 16 KiB."
            )
        content = req.bounded_stream.read(16385)
        if len(content) > 16384:
            raise falcon.HTTPPayloadTooLarge(
                description="Media metadata exceeds 16 KiB."
            )
        try:
            data = json.loads(content) if content else {}
        except (ValueError, UnicodeDecodeError) as error:
            raise DataError("Invalid JSON metadata.") from error
        if not isinstance(data, dict):
            raise DataError("Media metadata must be an object.")
        return data

    def _authorize_associations(self, req, media):
        user = cast(User, req.context["user"])
        for association in media.associations:
            if not user.can_read_fragment(
                self._fragments.query_read_scopes(association.fragment_id)
            ):
                raise falcon.HTTPForbidden()

    def _authorized_fragment(self, request: falcon.Request) -> MuseumNumber:
        value = request.get_param("fragment", required=True)
        if not isinstance(value, str) or not isinstance(
            request.params["fragment"], str
        ):
            raise DataError("A single fragment identifier is required.")
        number = parse_museum_number(value)
        scopes = self._fragments.query_read_scopes(number)
        user = cast(User, request.context["user"])
        if not user.can_read_fragment(scopes):
            raise falcon.HTTPForbidden()
        return number

    def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        _private_response(resp)
        number = self._authorized_fragment(req)
        management_view = req.get_param("view") == "management"
        if req.get_param("view") not in (None, "management"):
            raise DataError("Invalid media view.")
        if management_view:
            management, actor, manager, contributor = self._writer(req)
            media = management.list(number, actor, manager, contributor)
        else:
            media = self._runtime.service.list_fragment_media(number)
        resp.media = self._response(number, media, management=management_view)
        if not self._runtime.service.legacy_fallback_allowed(number):
            resp.media["legacyFallbackAllowed"] = False

    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        _private_response(resp)
        management, actor, _, _ = self._writer(req)
        number = self._authorized_fragment(req)
        header = req.get_header("X-Media-Metadata", required=True)
        if len(header) > 16384:
            raise falcon.HTTPPayloadTooLarge(
                description="Media metadata exceeds 16 KiB."
            )
        try:
            metadata = json.loads(unquote(header, errors="strict"))
        except (ValueError, UnicodeDecodeError) as error:
            raise DataError("Invalid media metadata header.") from error
        from ebl.media.infrastructure.upload_images import (
            UploadValidationError,
            UploadTooLargeError,
            UploadBusyError,
        )

        try:
            media, created = management.upload(
                number,
                actor,
                req.get_header("Idempotency-Key", required=True),
                metadata,
                req.bounded_stream,
                req.content_length,
                req.content_type,
            )
        except UploadTooLargeError as error:
            raise falcon.HTTPPayloadTooLarge(description=str(error)) from error
        except UploadBusyError as error:
            raise falcon.HTTPServiceUnavailable(
                description=str(error), retry_after=10
            ) from error
        except UploadValidationError as error:
            raise DataError(str(error)) from error
        except MediaConflictError as error:
            raise falcon.HTTPConflict(description=str(error)) from error
        resp.status = falcon.HTTP_201 if created else falcon.HTTP_200
        resp.media = self._response(number, (media,), management=True)

    def _mutate(self, req, resp, media_id, operation):
        _private_response(resp)
        management, actor, manager, _ = self._writer(
            req, manager_only=operation != "edit"
        )
        number = self._authorized_fragment(req)
        metadata = self._json_body(req)
        if operation != "edit":
            if set(metadata) - {"reason"} or (
                "reason" in metadata
                and (
                    not isinstance(metadata["reason"], str)
                    or len(metadata["reason"]) > 4000
                )
            ):
                raise DataError("Invalid review reason.")
        try:
            media = management.mutate(
                number,
                _media_id(media_id),
                actor,
                manager,
                operation,
                metadata,
                lambda item: self._authorize_associations(req, item),
            )
        except MediaPermissionError as error:
            raise falcon.HTTPForbidden(description=str(error)) from error
        except MediaConflictError as error:
            raise falcon.HTTPConflict(description=str(error)) from error
        if operation == "remove":
            resp.status = falcon.HTTP_204
        else:
            resp.media = self._response(number, (media,), management=True)

    def on_patch_item(self, req, resp, media_id):
        self._mutate(req, resp, media_id, "edit")

    def on_delete_item(self, req, resp, media_id):
        self._mutate(req, resp, media_id, "remove")

    def on_post_binary(self, req, resp, media_id, representation):
        if representation not in {"primary", "publish", "reject"}:
            raise falcon.HTTPNotFound()
        self._mutate(req, resp, media_id, representation)

    def on_get_binary(
        self,
        req: falcon.Request,
        resp: falcon.Response,
        media_id: str,
        representation: str,
        size: Optional[str] = None,
    ) -> None:
        _private_response(resp)
        if representation not in {"file", "display", "thumbnail"}:
            raise falcon.HTTPNotFound()
        number = self._authorized_fragment(req)
        identifier = _media_id(media_id)
        stored = self._runtime.service.get_stored_fragment_media(number, identifier)
        management = self._runtime.management
        if stored is None and management is not None:
            actor, manager, contributor = self._permissions(req)
            stored = management.get_stored(
                number, identifier, actor, manager, contributor
            )
        if stored is None:
            raise MediaNotFoundError(identifier)
        handle = _representation_handle(stored, representation, size)
        opened = self._runtime.store.open_representation(handle)
        if (
            opened.media_id != identifier
            or opened.representation != handle.representation
        ):
            opened.content.close()
            raise Defect("Invalid stored media representation.")
        resp.content_type = opened.representation.mime_type
        resp.content_length = opened.length
        if is_svg_mime_type(opened.representation.mime_type):
            resp.downloadable_as = f"{identifier}.svg"
            resp.set_header("Content-Security-Policy", "sandbox; default-src 'none'")
        resp.stream = opened.content

    def on_get_thumbnail(
        self,
        req: falcon.Request,
        resp: falcon.Response,
        media_id: str,
        size: str,
    ) -> None:
        self.on_get_binary(req, resp, media_id, "thumbnail", size)
