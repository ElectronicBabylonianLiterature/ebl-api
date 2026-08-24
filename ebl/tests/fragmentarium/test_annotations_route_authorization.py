import falcon
import pytest

from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.domain.annotation import Annotations
from ebl.tests.factories.fragment import TransliteratedFragmentFactory


@pytest.fixture
def restricted_fragment(fragmentarium):
    fragment = TransliteratedFragmentFactory.build(
        authorized_scopes=[Scope.READ_COPENHAGEN_FRAGMENTS]
    )
    fragmentarium.create(fragment)
    return fragment


@pytest.fixture
def readable_restricted_fragment(fragmentarium):
    fragment = TransliteratedFragmentFactory.build(
        authorized_scopes=[Scope.READ_CAIC_FRAGMENTS]
    )
    fragmentarium.create(fragment)
    return fragment


@pytest.fixture
def public_fragment(fragmentarium):
    fragment = TransliteratedFragmentFactory.build(authorized_scopes=[])
    fragmentarium.create(fragment)
    return fragment


def test_get_annotations_of_public_fragment_is_allowed(client, public_fragment):
    result = client.simulate_get(
        f"/fragments/{public_fragment.number}/annotations",
        params={"generateAnnotations": False},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json["fragmentNumber"] == str(public_fragment.number)


def test_get_annotations_of_public_fragment_is_allowed_for_guest(
    guest_client, public_fragment
):
    result = guest_client.simulate_get(
        f"/fragments/{public_fragment.number}/annotations",
        params={"generateAnnotations": False},
    )

    assert result.status == falcon.HTTP_OK


def test_get_annotations_of_authorized_restricted_fragment_is_allowed(
    client, readable_restricted_fragment
):
    result = client.simulate_get(
        f"/fragments/{readable_restricted_fragment.number}/annotations",
        params={"generateAnnotations": False},
    )

    assert result.status == falcon.HTTP_OK


def test_get_annotations_of_unauthorized_restricted_fragment_is_forbidden(
    client, restricted_fragment
):
    result = client.simulate_get(
        f"/fragments/{restricted_fragment.number}/annotations",
        params={"generateAnnotations": False},
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_get_annotations_of_restricted_fragment_is_forbidden_for_guest(
    guest_client, readable_restricted_fragment
):
    result = guest_client.simulate_get(
        f"/fragments/{readable_restricted_fragment.number}/annotations",
        params={"generateAnnotations": False},
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_generate_annotations_of_unauthorized_fragment_is_forbidden(
    client, restricted_fragment
):
    result = client.simulate_get(
        f"/fragments/{restricted_fragment.number}/annotations",
        params={"generateAnnotations": "true"},
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_annotations_of_unknown_fragment_stay_available(client):
    result = client.simulate_get(
        "/fragments/X.2/annotations", params={"generateAnnotations": False}
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == {
        "fragmentNumber": "X.2",
        "annotations": [],
    }


def test_empty_annotations_are_returned_for_public_fragment(client, public_fragment):
    expected = Annotations(public_fragment.number)

    result = client.simulate_get(
        f"/fragments/{public_fragment.number}/annotations",
        params={"generateAnnotations": False},
    )

    assert result.json["annotations"] == []
    assert result.json["fragmentNumber"] == str(expected.fragment_number)
