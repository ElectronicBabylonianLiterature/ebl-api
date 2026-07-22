from typing import Dict, List, Optional

from ebl.common.domain.project import ResearchProject
from ebl.fragmentarium.application.fragment_fields_schemas import (
    DossierReferenceSchema,
)
from ebl.fragmentarium.application.fragment_info_schema import ApiFragmentInfoSchema
from ebl.fragmentarium.application.fragment_query_summary_schema import (
    FragmentQuerySummarySchema,
)
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.fragmentarium.domain.fragment_query_summary import (
    FragmentQueryArchaeology,
    FragmentQuerySummary,
    matching_line_preview_of,
)
from ebl.tests.factories.provenance import build_provenance_records
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema


def get_provenance_record(record_id: str):
    return next(
        record for record in build_provenance_records() if record.id == record_id
    )


def expected_fragment_info_dto(fragment: Fragment, text=None) -> Dict:
    return ApiFragmentInfoSchema().dump(FragmentInfo.of(fragment, text))


def query_item_of(
    fragment: Fragment,
    matching_lines: Optional[List[int]] = None,
    match_count: Optional[int] = None,
) -> Dict:
    lines = [] if matching_lines is None else matching_lines

    return {
        "museumNumber": MuseumNumberSchema().dump(fragment.number),
        "matchingLines": lines,
        "matchCount": len(lines) if match_count is None else match_count,
    }


def query_result_of(
    items: List[Dict],
    match_count_total: Optional[int],
    is_match_count_total_exact: bool = True,
    has_next_page: Optional[bool] = None,
) -> Dict:
    return {
        "items": items,
        "matchCountTotal": match_count_total,
        "isMatchCountTotalExact": is_match_count_total_exact,
        "hasNextPage": has_next_page,
    }


def query_summary_of(
    fragment: Fragment,
    matching_lines: Optional[List[int]] = None,
    match_count: Optional[int] = None,
    has_photo: bool = False,
) -> Dict:
    lines = [] if matching_lines is None else matching_lines
    archaeology = (
        FragmentQueryArchaeology(
            excavation_number=fragment.archaeology.excavation_number,
            site=(
                fragment.archaeology.site.long_name
                if fragment.archaeology.site
                else None
            ),
        )
        if fragment.archaeology is not None
        else None
    )
    preview = matching_line_preview_of(fragment.text, lines)

    return FragmentQuerySummarySchema().dump(
        FragmentQuerySummary(
            museum_number=fragment.number,
            accession=fragment.accession,
            description=fragment.description,
            script=fragment.script,
            date=fragment.date,
            genres=fragment.genres,
            archaeology=archaeology,
            references=fragment.references,
            projects=tuple(
                project
                if isinstance(project, ResearchProject)
                else ResearchProject.from_abbreviation(str(project))
                for project in fragment.projects
            ),
            dossiers=tuple(
                DossierReferenceSchema().load(DossierReferenceSchema().dump(dossier))
                for dossier in fragment.dossiers
            ),
            matching_lines=tuple(lines),
            matching_line_preview=preview,
            match_count=len(lines) if match_count is None else match_count,
            has_photo=has_photo,
        )
    )
