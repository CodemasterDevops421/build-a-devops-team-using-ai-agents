import { FormEvent, useState } from 'react';
import './styles/app.css';
import { api, ApiError } from './services/api';
import { useAgentMutation } from './hooks/useAgentMutation';
import { Toast } from './components/Toast';
import { ResultPanel } from './components/ResultPanel';

const DEFAULT_GROQ_ENDPOINT = 'https://api.groq.com/v1';

type ToastState = {
  message: string;
  variant: 'success' | 'error';
};

export default function App() {
  const [toast, setToast] = useState<ToastState | null>(null);

  const optionalField = (value: string) => (value.trim().length ? value : undefined);

  const [ciForm, setCiForm] = useState({
    workflow_name: 'CI Pipeline',
    python_version: '3.12',
    run_tests: true,
    groq_api_endpoint: DEFAULT_GROQ_ENDPOINT,
    groq_api_key: '',
  });

  const [dockerForm, setDockerForm] = useState({
    base_image: 'python:3.12-slim',
    expose_port: 8000,
    copy_source: './',
    work_dir: '/app',
    groq_api_endpoint: DEFAULT_GROQ_ENDPOINT,
    groq_api_key: '',
  });

  const [predictForm, setPredictForm] = useState({
    model: 'heuristic',
    groq_api_key: '',
    build_id: 'build-001',
    commit_hash: 'abcdef1234567890',
    files_changed: 'app/main.py, agents/build_status_agent.py',
    tests_failed: false,
    coverage: 92,
  });

  const [statusForm, setStatusForm] = useState({
    image_tag: 'myapp:latest',
  });

  const ciMutation = useAgentMutation(api.generateCi);
  const dockerMutation = useAgentMutation(api.generateDockerfile);
  const predictMutation = useAgentMutation(api.predictBuild);
  const statusMutation = useAgentMutation(api.checkBuildStatus);

  const [pipelineYaml, setPipelineYaml] = useState<string | null>(null);
  const [dockerfileContent, setDockerfileContent] = useState<string | null>(null);
  const [predictionResult, setPredictionResult] = useState<Record<string, unknown> | null>(null);
  const [statusResult, setStatusResult] = useState<string | null>(null);

  const resetToast = () => setToast(null);
  const showSuccess = (message: string) => setToast({ message, variant: 'success' });
  const showError = (message: string) => setToast({ message, variant: 'error' });

  const loading = ciMutation.isPending || dockerMutation.isPending || predictMutation.isPending || statusMutation.isPending;

  const handleCiSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const result = await ciMutation.mutateAsync({
        ...ciForm,
        groq_api_endpoint: optionalField(ciForm.groq_api_endpoint),
        groq_api_key: optionalField(ciForm.groq_api_key),
      });
      setPipelineYaml(result.pipeline_yaml);
      showSuccess('CI workflow generated successfully.');
    } catch (error) {
      showError(error instanceof ApiError ? error.message : 'Failed to generate CI workflow');
    }
  };

  const handleDockerSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const result = await dockerMutation.mutateAsync({
        ...dockerForm,
        expose_port: Number(dockerForm.expose_port),
        groq_api_endpoint: optionalField(dockerForm.groq_api_endpoint),
        groq_api_key: optionalField(dockerForm.groq_api_key),
      });
      setDockerfileContent(result.dockerfile_content);
      showSuccess('Dockerfile generated successfully.');
    } catch (error) {
      showError(error instanceof ApiError ? error.message : 'Failed to generate Dockerfile');
    }
  };

  const handlePredictSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const files = predictForm.files_changed
        .split(/\r?\n|,/)
        .map((value) => value.trim())
        .filter(Boolean);

      const result = await predictMutation.mutateAsync({
        model: predictForm.model,
        groq_api_key: optionalField(predictForm.groq_api_key),
        build_data: {
          build_id: predictForm.build_id,
          commit_hash: predictForm.commit_hash,
          files_changed: files,
          tests_failed: predictForm.tests_failed,
          coverage: Number(predictForm.coverage),
        },
      });

      setPredictionResult(result.prediction);
      showSuccess('Build prediction generated successfully.');
    } catch (error) {
      showError(error instanceof ApiError ? error.message : 'Failed to predict build status');
    }
  };

  const handleStatusSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const result = await statusMutation.mutateAsync(statusForm);
      setStatusResult(result.status);
      showSuccess('Build status refreshed.');
    } catch (error) {
      showError(error instanceof ApiError ? error.message : 'Failed to fetch build status');
    }
  };

  const copyToClipboard = async (value: string | null) => {
    if (!value) return;
    try {
      await navigator.clipboard.writeText(value);
      showSuccess('Copied to clipboard.');
    } catch (error) {
      showError(error instanceof Error ? error.message : 'Unable to copy to clipboard');
    }
  };

  const hasSensitiveInput = Boolean(
    optionalField(ciForm.groq_api_key ?? '') ||
      optionalField(dockerForm.groq_api_key ?? '') ||
      optionalField(predictForm.groq_api_key ?? '')
  );

  return (
    <div className="app-container fade-in" aria-live="polite">
      <header className="header">
        <div>
          <h1>DevOps AI Control Center</h1>
          <p>
            Launch production-ready automation in seconds. Generate CI workflows, harden Dockerfiles, and predict build risk with
            a single command center designed for fast, secure DevOps execution.
          </p>
        </div>
        <div className="tag">{hasSensitiveInput ? 'Sensitive input not persisted' : 'Ready'}</div>
      </header>

      <section className="card-grid">
        <article className="agent-card">
          <div>
            <h2>CI/CD Orchestrator</h2>
            <p>Produce hardened GitHub Actions pipelines with linting, testing, and artifact workflows tuned for Python services.</p>
          </div>
          <form className="form-grid" onSubmit={handleCiSubmit}>
            <div className="field">
              <label htmlFor="workflow_name">Workflow Name</label>
              <input
                id="workflow_name"
                name="workflow_name"
                value={ciForm.workflow_name}
                onChange={(event) => setCiForm((prev) => ({ ...prev, workflow_name: event.target.value }))}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="python_version">Python Version</label>
              <input
                id="python_version"
                name="python_version"
                value={ciForm.python_version}
                onChange={(event) => setCiForm((prev) => ({ ...prev, python_version: event.target.value }))}
                required
              />
            </div>
            <label className="checkbox-row">
              <input
                type="checkbox"
                name="run_tests"
                checked={ciForm.run_tests}
                onChange={(event) => setCiForm((prev) => ({ ...prev, run_tests: event.target.checked }))}
              />
              Run pytest after installation
            </label>
            <div className="field">
              <label htmlFor="ci_groq_endpoint">Groq API Endpoint</label>
              <input
                id="ci_groq_endpoint"
                name="groq_api_endpoint"
                value={ciForm.groq_api_endpoint}
                onChange={(event) => setCiForm((prev) => ({ ...prev, groq_api_endpoint: event.target.value }))}
              />
            </div>
            <div className="field">
              <label htmlFor="ci_groq_key">Groq API Key</label>
              <input
                id="ci_groq_key"
                name="groq_api_key"
                type="password"
                value={ciForm.groq_api_key}
                onChange={(event) => setCiForm((prev) => ({ ...prev, groq_api_key: event.target.value }))}
                autoComplete="off"
              />
            </div>
            <button className="primary-button" type="submit" disabled={ciMutation.isPending}>
              {ciMutation.isPending ? 'Generating…' : 'Generate Workflow'}
            </button>
          </form>
          <ResultPanel
            title="Workflow YAML"
            result={pipelineYaml && <pre>{pipelineYaml}</pre>}
            onCopy={() => copyToClipboard(pipelineYaml)}
            copyDisabled={!pipelineYaml}
          />
        </article>

        <article className="agent-card">
          <div>
            <h2>Container Architect</h2>
            <p>Generate Dockerfiles with sane defaults, non-root execution, and production-grade caching guidance.</p>
          </div>
          <form className="form-grid" onSubmit={handleDockerSubmit}>
            <div className="field">
              <label htmlFor="base_image">Base Image</label>
              <input
                id="base_image"
                name="base_image"
                value={dockerForm.base_image}
                onChange={(event) => setDockerForm((prev) => ({ ...prev, base_image: event.target.value }))}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="expose_port">Expose Port</label>
              <input
                id="expose_port"
                name="expose_port"
                type="number"
                min="1"
                max="65535"
                value={dockerForm.expose_port}
                onChange={(event) => setDockerForm((prev) => ({ ...prev, expose_port: Number(event.target.value) }))}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="copy_source">Copy Source</label>
              <input
                id="copy_source"
                name="copy_source"
                value={dockerForm.copy_source}
                onChange={(event) => setDockerForm((prev) => ({ ...prev, copy_source: event.target.value }))}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="work_dir">Work Directory</label>
              <input
                id="work_dir"
                name="work_dir"
                value={dockerForm.work_dir}
                onChange={(event) => setDockerForm((prev) => ({ ...prev, work_dir: event.target.value }))}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="docker_groq_endpoint">Groq API Endpoint</label>
              <input
                id="docker_groq_endpoint"
                name="groq_api_endpoint"
                value={dockerForm.groq_api_endpoint}
                onChange={(event) => setDockerForm((prev) => ({ ...prev, groq_api_endpoint: event.target.value }))}
              />
            </div>
            <div className="field">
              <label htmlFor="docker_groq_key">Groq API Key</label>
              <input
                id="docker_groq_key"
                name="groq_api_key"
                type="password"
                value={dockerForm.groq_api_key}
                onChange={(event) => setDockerForm((prev) => ({ ...prev, groq_api_key: event.target.value }))}
                autoComplete="off"
              />
            </div>
            <button className="primary-button" type="submit" disabled={dockerMutation.isPending}>
              {dockerMutation.isPending ? 'Generating…' : 'Generate Dockerfile'}
            </button>
          </form>
          <ResultPanel
            title="Dockerfile"
            result={dockerfileContent && <pre>{dockerfileContent}</pre>}
            onCopy={() => copyToClipboard(dockerfileContent)}
            copyDisabled={!dockerfileContent}
          />
        </article>

        <article className="agent-card">
          <div>
            <h2>Build Risk Analyst</h2>
            <p>Predict rollout risk using repository context, test signals, and coverage deltas to prioritize fixes.</p>
          </div>
          <form className="form-grid" onSubmit={handlePredictSubmit}>
            <div className="field">
              <label htmlFor="model">Model</label>
              <input
                id="model"
                name="model"
                value={predictForm.model}
                onChange={(event) => setPredictForm((prev) => ({ ...prev, model: event.target.value }))}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="predict_groq_key">Groq API Key</label>
              <input
                id="predict_groq_key"
                name="groq_api_key"
                type="password"
                value={predictForm.groq_api_key}
                onChange={(event) => setPredictForm((prev) => ({ ...prev, groq_api_key: event.target.value }))}
                autoComplete="off"
              />
            </div>
            <div className="field">
              <label htmlFor="build_id">Build ID</label>
              <input
                id="build_id"
                name="build_id"
                value={predictForm.build_id}
                onChange={(event) => setPredictForm((prev) => ({ ...prev, build_id: event.target.value }))}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="commit_hash">Commit Hash</label>
              <input
                id="commit_hash"
                name="commit_hash"
                value={predictForm.commit_hash}
                onChange={(event) => setPredictForm((prev) => ({ ...prev, commit_hash: event.target.value }))}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="files_changed">Files Changed</label>
              <textarea
                id="files_changed"
                name="files_changed"
                value={predictForm.files_changed}
                onChange={(event) => setPredictForm((prev) => ({ ...prev, files_changed: event.target.value }))}
                placeholder="One path per line or comma separated"
              />
            </div>
            <label className="checkbox-row">
              <input
                type="checkbox"
                name="tests_failed"
                checked={predictForm.tests_failed}
                onChange={(event) => setPredictForm((prev) => ({ ...prev, tests_failed: event.target.checked }))}
              />
              Previous build had test failures
            </label>
            <div className="field">
              <label htmlFor="coverage">Coverage (%)</label>
              <input
                id="coverage"
                name="coverage"
                type="number"
                min="0"
                max="100"
                value={predictForm.coverage}
                onChange={(event) => setPredictForm((prev) => ({ ...prev, coverage: Number(event.target.value) }))}
                required
              />
            </div>
            <button className="primary-button" type="submit" disabled={predictMutation.isPending}>
              {predictMutation.isPending ? 'Scoring…' : 'Predict Risk'}
            </button>
          </form>
          <ResultPanel
            title="Prediction"
            result={
              predictionResult && (
                <pre>{JSON.stringify(predictionResult, null, 2)}</pre>
              )
            }
            onCopy={() => copyToClipboard(predictionResult ? JSON.stringify(predictionResult, null, 2) : null)}
            copyDisabled={!predictionResult}
          />
        </article>

        <article className="agent-card">
          <div>
            <h2>Release Pulse Monitor</h2>
            <p>Track container image readiness using deterministic heuristics, even when Docker is unavailable.</p>
          </div>
          <form className="form-grid" onSubmit={handleStatusSubmit}>
            <div className="field">
              <label htmlFor="image_tag">Image Tag</label>
              <input
                id="image_tag"
                name="image_tag"
                value={statusForm.image_tag}
                onChange={(event) => setStatusForm({ image_tag: event.target.value })}
                required
              />
            </div>
            <button className="primary-button" type="submit" disabled={statusMutation.isPending}>
              {statusMutation.isPending ? 'Checking…' : 'Check Status'}
            </button>
          </form>
          <ResultPanel
            title="Status"
            result={statusResult && <pre>{statusResult}</pre>}
            onCopy={() => copyToClipboard(statusResult)}
            copyDisabled={!statusResult}
          />
        </article>
      </section>

      {loading && <div aria-live="assertive" className="sr-only">Processing request…</div>}
      {toast && <Toast message={toast.message} variant={toast.variant} onClose={resetToast} />}
    </div>
  );
}
