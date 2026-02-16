from ebl.common.domain.project import ResearchProject
import pytest


def test_mapping():
    for project in ResearchProject:
        assert ResearchProject.from_name(project.long_name) == project
        assert ResearchProject.from_abbreviation(project.abbreviation) == project


def test_invalid_name():
    with pytest.raises(ValueError, match="Unknown ResearchProject.long_name: foobar"):
        ResearchProject.from_name("foobar")


def test_invalid_abbreviation():
    with pytest.raises(ValueError, match="Unknown ResearchProject.abbreviation: foo"):
        ResearchProject.from_abbreviation("foo")
