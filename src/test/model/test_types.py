from typing import List

from pydantic import BaseModel

from src.app.model.types import dict_diff


def test_dict_diff():
    diff = set(dict_diff(d1={"a": 1}, d2={"a": 2}))
    print(diff)
    assert diff == {("a", 2), ("a", 1)}
    diff = set(dict_diff(d1={"a": 1, "b": 3}, d2={"a": 1}))
    print(diff)
    assert diff == {("b", 3)}


def test_exclude_nested():
    class Track(BaseModel):
        id: int
        parent_id: int

    class Tracks(BaseModel):
        tracks: List[Track]

    class Project(BaseModel):
        composition: Tracks

    project = Project(composition=Tracks(tracks=[Track(id=1, parent_id=1), Track(id=2, parent_id=2)]))
    assert project.dict(exclude={"composition": {"tracks": {"__all__": {"parent_id"}}}}) == {
        "composition": {"tracks": [{"id": 1}, {"id": 2}]}
    }
