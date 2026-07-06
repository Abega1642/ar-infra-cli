from pydantic import BaseModel


class FeatureFilesSchema(BaseModel):
    shared_directories: list[str] = []
    specific_directories: list[str] = []
    shared_files: list[str] = []
    specific_files: list[str] = []
    shared_env_variables: list[str] = []
    specific_env_variables: list[str] = []


class FeatureDependenciesSchema(BaseModel):
    shared: list[str] = []
    specific: list[str] = []


class FeatureSchema(BaseModel):
    files: FeatureFilesSchema = FeatureFilesSchema()
    dependencies: FeatureDependenciesSchema = FeatureDependenciesSchema()


class DatabaseSharedSchema(BaseModel):
    directories: list[str] = []
    files: list[str] = []
    env_variables: list[str] = []
    dependencies: list[str] = []


class FeatureConfigSchema(BaseModel):
    src_package: str
    test_package: str
    database_shared: DatabaseSharedSchema
    features: dict[str, FeatureSchema]
