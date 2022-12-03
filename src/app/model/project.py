from __future__ import annotations

from typing import List, Iterator, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.app.model.project_version import ProjectVersion
from src.app.model.serializer import write_json_file, read_json_file
from src.app.model.types import get_one, Result
from src.app.utils.notification import notify
from src.app.utils.properties import NotificationMessage


class Project(BaseModel):
    name: str = ""
    file_name: Optional[str] = Field("", exclude=True)
    versions: List[ProjectVersion] = []

    def __iter__(self) -> Iterator[ProjectVersion]:
        return iter(self.versions)

    def __getitem__(self, item) -> ProjectVersion:
        return self.versions[item]

    def __len__(self):
        return len(self.versions)

    def get_version_by_name(self, version_name: str) -> ProjectVersion:
        return get_one(data=[version for version in self if version.name == version_name], raise_on_empty=True)

    def add_project_version(self, project_version: ProjectVersion) -> Project:
        self.versions.append(project_version)
        notify(message=NotificationMessage.PROJECT_VERSION_ADDED, project_version=project_version)
        return self

    def delete_project_version(self, project_version: ProjectVersion) -> Project:
        project_version.remove_all_tracks()
        notify(message=NotificationMessage.PROJECT_VERSION_REMOVED, project_version=project_version)
        self.versions.remove(project_version)
        return self

    def close_project(self):
        for project_version in self.versions:
            self.delete_project_version(project_version=project_version)
        return self

    def is_new_project_version_valid(self, new_name: str, exclude_id: Optional[UUID] = None) -> bool:
        pass

    def modify_project(self, project: Project) -> Project:
        self.name = project.name
        notify(message=NotificationMessage.PROJECT_CHANGED, project=project)
        return self

    def save_to_file(self, file_name: str) -> Optional[str]:
        if (
            result := write_json_file(
                json_dict=self.json(indent=2, exclude_none=True, exclude_defaults=True, exclude_unset=True),
                json_file_name=file_name,
            )
        ).error:
            return result.error
        self.file_name = file_name
        return None

    @classmethod
    def read_from_file(cls, file_name: str) -> Result[Project]:
        try:
            if (result := read_json_file(json_file_name=file_name)).error:
                return Result(error=result.error)
            project = Project(**result.value)
            project.file_name = file_name
            return Result(value=project)
        except IOError as e:
            return Result(error=str(e))


def empty_project() -> Project:
    return Project()


def new_project() -> Project:
    return Project(name="New project")
