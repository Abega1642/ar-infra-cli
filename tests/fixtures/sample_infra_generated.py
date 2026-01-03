INFRA_GENERATED_SAMPLE = """
package com.example.arinfra;

import static java.lang.annotation.ElementType.*;
import static java.lang.annotation.RetentionPolicy.RUNTIME;
import java.lang.annotation.Documented;
import java.lang.annotation.Retention;
import java.lang.annotation.Target;

@Documented
@Retention(RUNTIME)
@Target({TYPE, METHOD, CONSTRUCTOR})
public @interface InfraGenerated {
  String signature() default "ar-infra-cli";
  String version() default "1.0.0";
  String generatedAt() default "";
}
"""
