from ebl.transliteration.domain.labels import (
    ColumnLabel,
    LabelVisitor,
    LineNumberLabel,
    ObjectLabel,
    SurfaceLabel,
)


class LabelValidator(LabelVisitor):
    def __init__(self) -> None:
        self.has_surface = False
        self.has_column = False
        self.is_valid = True

    def visit_surface_label(self, label: SurfaceLabel) -> "LabelValidator":
        if self.has_surface or self.has_column:
            self.is_valid = False
        self.has_surface = True
        return self

    def visit_column_label(self, label: ColumnLabel) -> "LabelValidator":
        if self.has_column:
            self.is_valid = False
        self.has_column = True
        return self

    def visit_object_label(self, label: ObjectLabel) -> "LabelValidator":
        self.is_valid = False
        return self

    def visit_line_number_label(self, label: LineNumberLabel) -> "LabelValidator":
        self.is_valid = False
        return self
