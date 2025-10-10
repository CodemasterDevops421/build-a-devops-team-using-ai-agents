import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import App from './App';
import { api } from './services/api';

vi.mock('./services/api', () => {
  class ApiError extends Error {
    status: number;

    constructor(message: string, status: number) {
      super(message);
      this.status = status;
    }
  }

  return {
    ApiError,
    api: {
      generateCi: vi.fn().mockResolvedValue({ pipeline_yaml: 'name: ci', db_id: 1 }),
      generateDockerfile: vi.fn().mockResolvedValue({ dockerfile_content: 'FROM node:18-alpine', db_id: 2 }),
      predictBuild: vi.fn().mockResolvedValue({ prediction: { risk: 'low', score: 0.1 }, db_id: 3 }),
      checkBuildStatus: vi.fn().mockResolvedValue({ status: 'Succeeded', db_id: 4 }),
    },
  };
});

const renderApp = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  );
};

describe('App', () => {
  beforeEach(() => {
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
    Reflect.deleteProperty(navigator, 'clipboard');
  });

  it('submits CI generation form and renders result', async () => {
    renderApp();

    const [ciKeyInput] = screen.getAllByLabelText(/groq api key/i);
    fireEvent.change(ciKeyInput, { target: { value: 'test-ci-key' } });

    const submitButton = screen.getByRole('button', { name: /generate workflow/i });
    fireEvent.click(submitButton);

    await waitFor(() => expect(api.generateCi).toHaveBeenCalledTimes(1));
    expect(await screen.findByText(/CI workflow generated successfully/i)).toBeInTheDocument();
    expect(await screen.findByText(/name: ci/i)).toBeInTheDocument();
  });

  it('submits docker generation form and renders result', async () => {
    renderApp();

    const [, dockerKeyInput] = screen.getAllByLabelText(/groq api key/i);
    fireEvent.change(dockerKeyInput, { target: { value: 'test-docker-key' } });

    const submitButton = screen.getByRole('button', { name: /generate dockerfile/i });
    fireEvent.click(submitButton);

    await waitFor(() => expect(api.generateDockerfile).toHaveBeenCalledTimes(1));
    expect(await screen.findByText(/dockerfile generated successfully/i)).toBeInTheDocument();
    expect(await screen.findByText(/FROM node:18-alpine/i)).toBeInTheDocument();
  });

  it('submits build prediction form and renders json result', async () => {
    renderApp();

    const [, , predictKeyInput] = screen.getAllByLabelText(/groq api key/i);
    fireEvent.change(predictKeyInput, { target: { value: 'test-predict-key' } });

    const submitButton = screen.getByRole('button', { name: /predict risk/i });
    fireEvent.click(submitButton);

    await waitFor(() => expect(api.predictBuild).toHaveBeenCalledTimes(1));
    expect(await screen.findByText(/build prediction generated successfully/i)).toBeInTheDocument();
    expect(await screen.findByText(/"risk": "low"/i)).toBeInTheDocument();
  });

  it('submits build status form and renders status', async () => {
    renderApp();

    const submitButton = screen.getByRole('button', { name: /check status/i });
    fireEvent.click(submitButton);

    await waitFor(() => expect(api.checkBuildStatus).toHaveBeenCalledTimes(1));
    expect(await screen.findByText(/build status refreshed/i)).toBeInTheDocument();
    expect(await screen.findByText(/Succeeded/i)).toBeInTheDocument();
  });
});
