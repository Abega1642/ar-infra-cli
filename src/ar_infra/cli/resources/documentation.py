SKIP_COMMAND = """
Skip the GitHub App installation prompt. Use this flag if you want to install ar-infra-bot later.
"""

GROUP_OPTION_HELP = """
Gradle group ID for the generated project.

This value is used as the base namespace for your project and usually
corresponds to your organization or domain name in reverse notation
(e.g. "com.example", "dev.razafindratelo").

It will typically be used to:
- Define the project's group in Gradle
- Prefix Java/Kotlin package names

Example:
  --group=dev.razafindratelo
"""

ARTIFACT_OPTION_HELP = """
Gradle artifact ID for the project.

This value uniquely identifies the project within the given group
and is typically used as:
- The Gradle artifact name
- The base project/module name

It should be lowercase and may contain hyphens.

Example:
  --artifact=feature-test
"""

VERSION_OPTION_HELP = """
Project version.

This value defines the version of the generated project and is used
by Gradle for dependency resolution and publishing.

Semantic versioning is recommended.

Example:
  --project-version=1.0.0
"""

PATH_OPTION_HELP = """
Destination directory where the project will be generated.

If the directory does not exist, it will be created.
If omitted, the current working directory is used.

Example:
  --path=~/projects
"""

PROJECT_DIR_OPTION_HELP = """
Project directory name.

This is the name of the folder that will contain the generated project.
By default, it may be derived from the artifact ID.

Example:
  --project-dir=my-app
"""

FEATURES_OPTION_HELP = """
Comma-separated list of features to enable.

Features control optional components or configurations included
in the generated project.

Example:
  --features=postgresql,s3_bucket,rabbitmq,
"""

NO_FEATURES_OPTION_HELP = """
Comma-separated list of features to disable.

This option explicitly disables features that may be enabled
by default or via templates.

Example:
  --disable-features=rabbitmq
"""

NO_CACHE_OPTION_HELP = """
Disable template cache.

Forces the tool to re-download the template instead of using
a locally cached version.

Useful when the template has been updated.

Example:
  --no-cache
"""
