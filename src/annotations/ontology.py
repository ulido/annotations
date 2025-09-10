from __future__ import annotations
from collections.abc import Collection

from annotations import Annotation, AnnotationCollection


class OntologyEntry:
    """Describes an entry / level of an annotation ontology.
    """
    name: str
    synonyms: tuple[str]
    comment: str | None
    ident: str | None
    goterm: str | None
    children: set[OntologyEntry]
    parent: OntologyEntry | None
    examples: list[str]

    def __init__(
        self,
        name: str,
        synonyms: tuple[str] | None = None,
        comment: str | None = None,
        ident: str | None = None,
        goterm: str | None = None,
        examples: list[str] | None = None,
    ):
        """Create a new ontology entry.

        Args:
            name: Name of the entry.
            synonyms: Tuple of synonyms of the entry.
            comment: Comment associated with the entry.
            ident: N/A
            goterm: GO term identifier.
            examples: List of examples that can be associated with this entry.
        """
        self.name = name
        if synonyms is not None:
            self.synonyms = tuple(synonyms)
        else:
            self.synonyms = tuple()
        self.comment = comment
        self.ident = ident
        self.goterm = goterm
        self.children = set()
        self.parent = None
        if examples is not None:
            self.examples = examples
        else:
            self.examples = []

    def set_parent(self, parent: OntologyEntry):
        """Set this entry's parent ontology entry."""
        self.parent = parent

    def add_child(self, child: OntologyEntry):
        """Add a child ontology entry to this entry."""
        self.children.add(child)

    def __hash__(self):
        return hash((self.__class__, self.name))

    def match_term(self, term: str, recursive: bool = True) -> bool:
        """Returns whether the given term matches the entry's name. Returns
        `True` if any of the entries descendents match if `recursive` is
        `True`

        Args:
            term: Term to check then name against.
            recursive: Whether to recursively check the entries children.
        """
        if self.name == term:
            return True
        if recursive and self.parent is not None:
            return self.parent.match_term(term, recursive=True)
        return False


class Ontology:
    """Describes an Annotation ontology tree.
    """
    root_entries: list[OntologyEntry]
    """The root entries of the ontology."""
    entries: dict[str, OntologyEntry]
    """Name to entry mapping of all ontology entries."""

    def __init__(self):
        """Create a new `Ontology` object."""
        self.root_entries = []
        self.entries = {}


class OntologyAnnotation(Annotation):
    """Annotation object that is connected to an annotation ontology."""
    def __init__(self, annotation_string: str, ontology: Ontology):
        """Create an annotation entry object.

        Args:
            annotation_string: An annotation string of the form
                "term[modifier1,modifier2]".
            ontology: Ontology to use for the annotation.
        """
        super().__init__(annotation_string)
        self.ontology_entry = ontology.entries[self.term]

    def _match_term(self, term, recursive: bool = True):
        return self.ontology_entry.match_term(term, recursive=recursive)


def _ontology_annotation_factory(a_str: str, ontology: Ontology):
    return OntologyAnnotation(a_str, ontology)


class OntologyAnnotationCollection(AnnotationCollection):
    """Annotation collection that is connected to an annotation ontology.
    """
    def __init__(self, annotations_string: str, ontology: Ontology):
        """Create an annotation entry object.

        Args:
            annotations_string: Annotation string of the form
                "cytoplasm[points,weak],nucleoplasm".
            ontology: Ontology to use for the annotations.
        """
        self.ontology = ontology
        super().__init__(
            annotations_string,
            _ontology_annotation_factory,
            (ontology,),
        )

    def __and__(self, other: OntologyAnnotationCollection):
        intersection = self._annotations & other._annotations
        result = OntologyAnnotationCollection("", self.ontology)
        result._annotations = intersection
        return result

    def __or__(self, other: OntologyAnnotationCollection):
        union = self._annotations | other._annotations
        result = OntologyAnnotationCollection("", self.ontology)
        result._annotations = union
        return result

    def match(
        self,
        term: str,
        require_modifiers: set[str] | None = None,
        exclude_modifiers: set[str] | None = None,
        recursive: bool = True,
        *args, **kwargs,
    ):
        """Returns whether any `Annotation` in the collection matches the given
        term. Optionally allows specifying modifiers that need to be present
        or cannot be present for a positive match. This also matches any
        children of the given ontology term recursively if `recursive` is
        `True` (the default).

        Internally, this calls `Annotation.match` on each of the `Annotation`
        objects in the collection until it finds a positive match.

        Args:
            term: Annotation term to match.
            require_modifiers: Set of modifiers that need to be present for a
                positive match. No required modifiers assumed if `None`.
            exclude_modifiers: Set of modifiers that lead to a negative match
                if any of them are present.
            recursive: Whether to match the children of the given ontology
                term as well.
        """
        return super().match(
            term,
            require_modifiers=require_modifiers,
            exclude_modifiers=exclude_modifiers,
            recursive=recursive,
            *args, **kwargs,
        )

    def new_from_collection(
        self,
        annotations: Collection[OntologyAnnotation],
    ):
        """Returns a new OntologyAnnotationCollection from the given list of
        `OntologyAnnotation` objects."""
        new = OntologyAnnotationCollection("", self.ontology)
        new._annotations = frozenset(annotations)
        return new
