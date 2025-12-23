"""Test fixtures for Gradle build files."""

SAMPLE_BUILD_GRADLE = """
plugins {
    id 'java'
    id 'org.springframework.boot' version '3.2.0'
    id 'io.spring.dependency-management' version '1.1.4'
}

group = 'com.example'
version = '0.0.1-SNAPSHOT'

java {
    sourceCompatibility = '21'
}

configurations {
    compileOnly {
        extendsFrom annotationProcessor
    }
}

repositories {
    mavenCentral()
}

dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    compileOnly 'org.projectlombok:lombok'
    annotationProcessor 'org.projectlombok:lombok'
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
}

tasks.named('test') {
    useJUnitPlatform()
}
"""

SAMPLE_SETTINGS_GRADLE = """
rootProject.name = 'arInfra'
"""

MALICIOUS_BUILD_GRADLE = """
plugins {
    id 'java'
}

group = 'com.example"; System.exit(0); //'
version = '0.0.1'

dependencies {
    implementation '../../../etc/passwd'
}
"""

BUILD_GRADLE_WITHOUT_DEPENDENCIES = """
plugins {
    id 'java'
}

group = 'com.example'
version = '1.0.0'

repositories {
    mavenCentral()
}
"""
