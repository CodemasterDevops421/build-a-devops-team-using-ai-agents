import { z } from 'zod';

const baseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000';

const responseSchema = z
  .object({
    error: z.union([z.string(), z.undefined()]).optional(),
  })
  .passthrough();

export class ApiError extends Error {
  public readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<TResponse>(
  path: string,
  options: RequestInit & { signal?: AbortSignal }
): Promise<TResponse> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);

  try {
    const response = await fetch(`${baseUrl}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers ?? {}),
      },
      signal: options.signal ?? controller.signal,
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const errorDetail = (body as { detail?: string }).detail;
      throw new ApiError(errorDetail ?? `Request failed with status ${response.status}`, response.status);
    }

    const json = (await response.json()) as TResponse;
    responseSchema.parse(json, { path: [] });
    return json;
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError('Request timed out', 408);
    }
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(error instanceof Error ? error.message : 'Unexpected error occurred', 500);
  } finally {
    clearTimeout(timeout);
  }
}

export const api = {
  generateCi: (payload: {
    workflow_name: string;
    python_version: string;
    run_tests: boolean;
    groq_api_endpoint?: string | null;
    groq_api_key?: string | null;
  }) =>
    request<{ pipeline_yaml: string; db_id: number }>('/devops/generate-ci', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  generateDockerfile: (payload: {
    base_image: string;
    expose_port: number;
    copy_source: string;
    work_dir: string;
    groq_api_endpoint?: string | null;
    groq_api_key?: string | null;
  }) =>
    request<{ dockerfile_content: string; db_id: number }>('/devops/generate-dockerfile', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  predictBuild: (payload: {
    model: string;
    groq_api_key?: string | null;
    build_data: {
      build_id: string;
      commit_hash: string;
      files_changed: string[];
      tests_failed: boolean;
      coverage: number;
    };
  }) =>
    request<{ prediction: Record<string, unknown>; db_id: number }>('/devops/predict-build', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  checkBuildStatus: (payload: { image_tag: string }) =>
    request<{ status: string; db_id: number }>('/devops/check-build-status', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
