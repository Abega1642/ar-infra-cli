API_EXCEPTION_HANDLER_SAMPLE = """
package com.example.arinfra.endpoint.rest.controller;

import com.example.arinfra.exception.bucket.BucketHealthCheckException;
import com.example.arinfra.exception.bucket.BucketOperationException;
import com.example.arinfra.exception.health.EmailHealthCheckException;
import jakarta.persistence.EntityNotFoundException;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

@ControllerAdvice
@Sl4j
public class ApiExceptionHandler {

  @ExceptionHandler(BucketHealthCheckException.class)
  public ResponseEntity<ErrorResponse> handleBucketHealthCheckException(
      BucketHealthCheckException ex, WebRequest request) {

    log.error(
        "Bucket health check failed at path: {}, error code: {}",
        forJava(getRequestPath(request)),
        forJava(ex.getErrorCode()),
        ex);

    var errorResponse =
        ErrorResponse.of(
            HttpStatus.SERVICE_UNAVAILABLE,
            ex.getMessage(),
            getRequestPath(request),
            ex.getErrorCode());

    return new ResponseEntity<>(errorResponse, HttpStatus.SERVICE_UNAVAILABLE);
  }

  @ExceptionHandler(EmailHealthCheckException.class)
  public ResponseEntity<ErrorResponse> handleEmailHealthCheckException(
      EmailHealthCheckException ex, WebRequest request) {

    log.error(
        "Email health check failed at path: {}, test case: {}",
        forJava(getRequestPath(request)),
        forJava(ex.getTestCaseName()),
        ex);

    String errorMessage =
        format(
            "Email health check failed at test case '%s': %s",
            ex.getTestCaseName(),
            ex.getCause() != null ? ex.getCause().getMessage() : ex.getMessage());

    var errorResponse =
        ErrorResponse.of(
            HttpStatus.INTERNAL_SERVER_ERROR,
            errorMessage,
            getRequestPath(request),
            "EMAIL_HEALTH_CHECK_FAILED");

    return new ResponseEntity<>(errorResponse, HttpStatus.INTERNAL_SERVER_ERROR);
  }

  @ExceptionHandler(EntityNotFoundException.class)
  public ResponseEntity<ErrorResponse> handleEntityNotFoundException(
      EntityNotFoundException ex, WebRequest request) {

    log.warn(
        "Entity not found at path: {}, reason: {}",
        forJava(getRequestPath(request)),
        forJava(ex.getMessage()));

    var errorResponse =
        ErrorResponse.of(
            HttpStatus.NOT_FOUND, ex.getMessage(), getRequestPath(request), "ENTITY_NOT_FOUND");
    return new ResponseEntity<>(errorResponse, HttpStatus.NOT_FOUND);
  }

  @ExceptionHandler(BucketOperationException.class)
  public ResponseEntity<ErrorResponse> handleBucketOperationException(
      BucketOperationException ex, WebRequest request) {

    log.error(
        "Bucket operation failed at path: {}, error code: {}",
        forJava(getRequestPath(request)),
        forJava(ex.getErrorCode()),
        ex);

    var errorResponse =
        ErrorResponse.of(
            HttpStatus.INTERNAL_SERVER_ERROR,
            ex.getMessage(),
            getRequestPath(request),
            ex.getErrorCode());

    return new ResponseEntity<>(errorResponse, HttpStatus.INTERNAL_SERVER_ERROR);
  }

  @ExceptionHandler(Exception.class)
  public ResponseEntity<ErrorResponse> handleGenericException(Exception ex, WebRequest request) {
    log.error(
        "Unexpected error at path: {}, exception type: {}, message: {}",
        forJava(getRequestPath(request)),
        forJava(ex.getClass().getName()),
        forJava(ex.getMessage()),
        ex);

    var errorResponse =
        ErrorResponse.of(
            HttpStatus.INTERNAL_SERVER_ERROR,
            "An internal server error occurred",
            getRequestPath(request),
            "INTERNAL_SERVER_ERROR");
    return new ResponseEntity<>(errorResponse, HttpStatus.INTERNAL_SERVER_ERROR);
  }

  @ExceptionHandler(ConstraintViolationException.class)
  public ResponseEntity<ErrorResponse> handleConstraintViolationException(
      ConstraintViolationException ex, WebRequest request) {

    String message =
        ex.getConstraintViolations().stream()
            .map(violation -> violation.getPropertyPath() + ": " + violation.getMessage())
            .collect(Collectors.joining(", "));

    log.warn(
        "Constraint violation at path: {}, violations: {}",
        forJava(getRequestPath(request)),
        forJava(message));

    var errorResponse =
        ErrorResponse.of(
            HttpStatus.BAD_REQUEST, message, getRequestPath(request), "INVALID_PARAMETER");

    return new ResponseEntity<>(errorResponse, HttpStatus.BAD_REQUEST);
  }

  @ExceptionHandler(HandlerMethodValidationException.class)
  public ResponseEntity<ErrorResponse> handleHandlerMethodValidationException(
      HandlerMethodValidationException ex, WebRequest request) {

    log.warn(
        "Handler method validation failed at path: {}, message: {}",
        forJava(getRequestPath(request)),
        forJava(ex.getMessage()));

    var errorResponse =
        ErrorResponse.of(
            HttpStatus.BAD_REQUEST, ex.getMessage(), getRequestPath(request), "VALIDATION_ERROR");

    return new ResponseEntity<>(errorResponse, HttpStatus.BAD_REQUEST);
  }

  private String getRequestPath(WebRequest request) {
    if (request instanceof ServletWebRequest servletWebRequest)
      return servletWebRequest.getRequest().getRequestURI();

    return "N/A";
  }
}
"""
