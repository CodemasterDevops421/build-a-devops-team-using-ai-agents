import { useMutation, UseMutationResult } from '@tanstack/react-query';
import { ApiError } from '../services/api';

export function useAgentMutation<TInput, TResult>(
  mutationFn: (payload: TInput) => Promise<TResult>
): UseMutationResult<TResult, ApiError, TInput, unknown> {
  return useMutation<TResult, ApiError, TInput>({
    mutationFn,
  });
}
