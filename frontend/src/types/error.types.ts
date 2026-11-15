export interface ValidationError extends ApiError {
  fields: Record<string, string[]>;
}

export interface NetworkError extends ApiError {
  isNetworkError: true;
  originalError: Error;
}

export interface ApiError<TDetails = unknown> {
  message: string;
  status: number;
  code?: string;
  details?: TDetails;
  timestamp: string;
}

export class ApiException<TDetails = unknown> extends Error {
  public status: number;
  public code?: string;
  public details?: TDetails;

  constructor(error: ApiError<TDetails>) {
    super(error.message);
    this.name = "ApiException";
    this.status = error.status;
    this.code = error.code;
    this.details = error.details;
  }
}
