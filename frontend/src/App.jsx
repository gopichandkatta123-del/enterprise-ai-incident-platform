import { useEffect, useMemo, useState } from 'react'
import './App.css'

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  'http://127.0.0.1:8000'

function App() {
  const [incidents, setIncidents] = useState([])
  const [agentRuns, setAgentRuns] = useState([])
  const [decisions, setDecisions] = useState([])

  const [selectedIncidentId, setSelectedIncidentId] = useState(null)

  const [analysis, setAnalysis] = useState(null)

  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [savingDecision, setSavingDecision] = useState(false)

  const [reviewerName, setReviewerName] = useState('Gopichand')
  const [reviewNotes, setReviewNotes] = useState('')

  const [error, setError] = useState('')

  const selectedIncident = useMemo(
    () =>
      incidents.find(
        (incident) => incident.id === selectedIncidentId
      ),
    [incidents, selectedIncidentId]
  )

  const latestRun = agentRuns[0]

  const currentDecision = useMemo(() => {
    if (!analysis?.agent_run_id) {
      return null
    }

    return decisions.find(
      (decision) =>
        decision.agent_run_id === analysis.agent_run_id
    )
  }, [decisions, analysis])

  async function loadDashboard() {
    try {
      setLoading(true)
      setError('')

      const [
        incidentsResponse,
        runsResponse,
        decisionsResponse,
      ] = await Promise.all([
        fetch(`${API_BASE}/incidents`),
        fetch(`${API_BASE}/agent-runs`),
        fetch(`${API_BASE}/remediation-decisions`),
      ])

      if (
        !incidentsResponse.ok ||
        !runsResponse.ok ||
        !decisionsResponse.ok
      ) {
        throw new Error('Unable to load backend data.')
      }

      const incidentData =
        await incidentsResponse.json()

      const runData =
        await runsResponse.json()

      const decisionData =
        await decisionsResponse.json()

      setIncidents(incidentData)
      setAgentRuns(runData)
      setDecisions(decisionData)

      if (
        !selectedIncidentId &&
        incidentData.length > 0
      ) {
        setSelectedIncidentId(
          incidentData[0].id
        )
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function runAgentAnalysis() {
    if (!selectedIncidentId) {
      return
    }

    try {
      setAnalyzing(true)
      setError('')
      setReviewNotes('')

      const response = await fetch(
        `${API_BASE}/incidents/${selectedIncidentId}/agent-analyze`,
        {
          method: 'POST',
          headers: {
            Accept: 'application/json',
          },
        }
      )

      const data = await response.json()

      if (!response.ok || data.error) {
        throw new Error(
          data.error ||
            'Agent analysis failed.'
        )
      }

      setAnalysis(data)

      await loadDashboard()
    } catch (err) {
      setError(err.message)
    } finally {
      setAnalyzing(false)
    }
  }

  async function submitDecision(decisionValue) {
    if (!analysis?.agent_run_id) {
      setError(
        'Run an agent analysis before submitting a remediation decision.'
      )
      return
    }

    if (!reviewerName.trim()) {
      setError(
        'Please enter the reviewer name.'
      )
      return
    }

    try {
      setSavingDecision(true)
      setError('')

      const response = await fetch(
        `${API_BASE}/agent-runs/${analysis.agent_run_id}/decision`,
        {
          method: 'POST',
          headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            decision: decisionValue,
            approved_by: reviewerName.trim(),
            notes: reviewNotes.trim() || null,
          }),
        }
      )

      const data = await response.json()

      if (!response.ok || data.error) {
        throw new Error(
          data.error ||
            'Unable to save remediation decision.'
        )
      }

      setDecisions((current) => {
        const remaining =
          current.filter(
            (item) =>
              item.agent_run_id !==
              data.agent_run_id
          )

        return [
          data,
          ...remaining,
        ]
      })

      setReviewNotes('')
    } catch (err) {
      setError(err.message)
    } finally {
      setSavingDecision(false)
    }
  }

  useEffect(() => {
    loadDashboard()
  }, [])

  return (
    <main className="dashboard">
      <header className="topbar">
        <div>
          <p className="eyebrow">
            AI Operations Platform
          </p>

          <h1>
            Enterprise Agentic AI
            <span>
              {' '}
              Incident Intelligence
            </span>
          </h1>

          <p className="subtitle">
            Multi-agent incident diagnosis,
            RAG retrieval, guardrails,
            remediation planning, human
            approval, and observability.
          </p>
        </div>

        <div className="health-badge">
          <span className="health-dot" />
          Backend connected
        </div>
      </header>

      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}

      <section className="metrics-grid">
        <MetricCard
          label="Incidents"
          value={incidents.length}
          helper="Persistent PostgreSQL records"
        />

        <MetricCard
          label="Agent Runs"
          value={agentRuns.length}
          helper="LangGraph executions"
        />

        <MetricCard
          label="Latest Evaluation"
          value={
            latestRun?.evaluation_score !=
            null
              ? `${Math.round(
                  latestRun.evaluation_score *
                    100
                )}%`
              : '—'
          }
          helper={
            latestRun?.guardrail_decision ||
            'No evaluation yet'
          }
        />

        <MetricCard
          label="Latest Latency"
          value={
            latestRun?.latency_ms
              ? `${(
                  latestRun.latency_ms /
                  1000
                ).toFixed(2)}s`
              : '—'
          }
          helper="End-to-end agent execution"
        />
      </section>

      <section className="workspace-grid">
        <div className="panel incidents-panel">
          <div className="panel-header">
            <div>
              <p className="section-label">
                Incident Queue
              </p>

              <h2>
                Production Incidents
              </h2>
            </div>

            <button
              className="secondary-button"
              onClick={loadDashboard}
            >
              Refresh
            </button>
          </div>

          {loading ? (
            <p className="muted">
              Loading incidents...
            </p>
          ) : (
            <div className="incident-list">
              {incidents.map(
                (incident) => (
                  <button
                    key={incident.id}
                    className={`incident-item ${
                      selectedIncidentId ===
                      incident.id
                        ? 'active'
                        : ''
                    }`}
                    onClick={() => {
                      setSelectedIncidentId(
                        incident.id
                      )

                      setAnalysis(null)
                      setReviewNotes('')
                    }}
                  >
                    <div className="incident-row">
                      <strong>
                        #{incident.id}{' '}
                        {
                          incident.service_name
                        }
                      </strong>

                      <SeverityBadge
                        severity={
                          incident.severity
                        }
                      />
                    </div>

                    <p>
                      {
                        incident.error_message
                      }
                    </p>
                  </button>
                )
              )}
            </div>
          )}
        </div>

        <div className="panel investigation-panel">
          <div className="panel-header">
            <div>
              <p className="section-label">
                Agentic Investigation
              </p>

              <h2>
                {selectedIncident
                  ? `Incident #${selectedIncident.id}`
                  : 'Select an incident'}
              </h2>
            </div>

            <button
              className="primary-button"
              onClick={runAgentAnalysis}
              disabled={
                analyzing ||
                !selectedIncidentId
              }
            >
              {analyzing
                ? 'Analyzing...'
                : 'Run Agent Analysis'}
            </button>
          </div>

          {selectedIncident && (
            <div className="incident-summary">
              <div>
                <span>Service</span>

                <strong>
                  {
                    selectedIncident.service_name
                  }
                </strong>
              </div>

              <div>
                <span>Severity</span>

                <strong>
                  {
                    selectedIncident.severity
                  }
                </strong>
              </div>

              <div>
                <span>Error</span>

                <strong>
                  {
                    selectedIncident.error_message
                  }
                </strong>
              </div>
            </div>
          )}

          {!analysis ? (
            <div className="empty-state">
              <div className="agent-orb">
                AI
              </div>

              <h3>
                Ready for investigation
              </h3>

              <p>
                Select an incident and run
                the LangGraph workflow to
                generate diagnosis, RAG
                context, evaluation,
                remediation, and a human
                approval decision.
              </p>
            </div>
          ) : (
            <AnalysisView
              analysis={analysis}
              decision={
                currentDecision
              }
              reviewerName={
                reviewerName
              }
              setReviewerName={
                setReviewerName
              }
              reviewNotes={
                reviewNotes
              }
              setReviewNotes={
                setReviewNotes
              }
              submitDecision={
                submitDecision
              }
              savingDecision={
                savingDecision
              }
            />
          )}
        </div>
      </section>

      <section className="panel runs-panel">
        <div className="panel-header">
          <div>
            <p className="section-label">
              Observability
            </p>

            <h2>
              Agent Run History
            </h2>
          </div>
        </div>

        <div className="runs-table-wrapper">
          <table className="runs-table">
            <thead>
              <tr>
                <th>Run</th>
                <th>Incident</th>
                <th>Status</th>
                <th>Supervisor</th>
                <th>Evaluation</th>
                <th>Guardrail</th>
                <th>Decision</th>
                <th>Latency</th>
              </tr>
            </thead>

            <tbody>
              {agentRuns.map(
                (run) => {
                  const decision =
                    decisions.find(
                      (item) =>
                        item.agent_run_id ===
                        run.id
                    )

                  return (
                    <tr key={run.id}>
                      <td>
                        #{run.id}
                      </td>

                      <td>
                        #{run.incident_id}
                      </td>

                      <td>
                        <span className="status-success">
                          {run.status}
                        </span>
                      </td>

                      <td>
                        {
                          run.supervisor_decision
                        }
                      </td>

                      <td>
                        {run.evaluation_score !=
                        null
                          ? `${Math.round(
                              run.evaluation_score *
                                100
                            )}%`
                          : '—'}
                      </td>

                      <td>
                        {
                          run.guardrail_decision
                        }
                      </td>

                      <td>
                        {decision ? (
                          <DecisionBadge
                            decision={
                              decision.decision
                            }
                          />
                        ) : (
                          <span className="decision-pending">
                            pending
                          </span>
                        )}
                      </td>

                      <td>
                        {(
                          run.latency_ms /
                          1000
                        ).toFixed(2)}
                        s
                      </td>
                    </tr>
                  )
                }
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  )
}

function MetricCard({
  label,
  value,
  helper,
}) {
  return (
    <article className="metric-card">
      <p>{label}</p>
      <strong>{value}</strong>
      <span>{helper}</span>
    </article>
  )
}

function SeverityBadge({ severity }) {
  const value =
    severity?.toLowerCase() ||
    'unknown'

  return (
    <span
      className={`severity severity-${value}`}
    >
      {severity}
    </span>
  )
}

function DecisionBadge({ decision }) {
  return (
    <span
      className={`decision-badge decision-${decision}`}
    >
      {decision}
    </span>
  )
}

function AnalysisView({
  analysis,
  decision,
  reviewerName,
  setReviewerName,
  reviewNotes,
  setReviewNotes,
  submitDecision,
  savingDecision,
}) {
  const diagnosis =
    analysis.agent_diagnosis || {}

  const evaluation =
    analysis.evaluation || {}

  const remediation =
    analysis.remediation_plan || {}

  const logAnalysis =
    analysis.log_analysis || {}

  return (
    <div className="analysis-stack">
      <div className="analysis-grid">
        <div className="analysis-card">
          <span>Supervisor</span>

          <strong>
            {
              analysis.supervisor_decision
            }
          </strong>
        </div>

        <div className="analysis-card">
          <span>Evaluation</span>

          <strong>
            {evaluation.score != null
              ? `${Math.round(
                  evaluation.score *
                    100
                )}%`
              : '—'}
          </strong>
        </div>

        <div className="analysis-card">
          <span>Guardrail</span>

          <strong>
            {
              evaluation.guardrail_decision ||
              '—'
            }
          </strong>
        </div>

        <div className="analysis-card">
          <span>Latency</span>

          <strong>
            {analysis.latency_ms
              ? `${(
                  analysis.latency_ms /
                  1000
                ).toFixed(2)}s`
              : '—'}
          </strong>
        </div>
      </div>

      <div className="diagnosis-card">
        <p className="section-label">
          AI Root Cause Diagnosis
        </p>

        <h3>
          {
            diagnosis.probable_root_cause ||
            'No diagnosis'
          }
        </h3>

        <p>
          {diagnosis.explanation}
        </p>

        <div className="confidence-row">
          <span>Confidence</span>

          <strong>
            {diagnosis.confidence !=
            null
              ? `${Math.round(
                  diagnosis.confidence *
                    100
                )}%`
              : '—'}
          </strong>
        </div>
      </div>

      <div className="two-column">
        <div className="subpanel">
          <p className="section-label">
            Log Analysis
          </p>

          <h3>
            {
              logAnalysis.probable_log_cause ||
              'No log pattern'
            }
          </h3>

          <p>
            Confidence:{' '}
            {logAnalysis.confidence !=
            null
              ? `${Math.round(
                  logAnalysis.confidence *
                    100
                )}%`
              : '—'}
          </p>

          <ul>
            {(
              logAnalysis.patterns ||
              []
            ).map(
              (pattern) => (
                <li key={pattern}>
                  {pattern}
                </li>
              )
            )}
          </ul>
        </div>

        <div className="subpanel">
          <p className="section-label">
            Retrieved Runbooks
          </p>

          {(
            analysis.retrieved_runbooks ||
            []
          ).length > 0 ? (
            (
              analysis.retrieved_runbooks ||
              []
            ).map(
              (runbook) => (
                <div
                  className="runbook-result"
                  key={runbook.id}
                >
                  <strong>
                    {runbook.title}
                  </strong>

                  <span>
                    Similarity{' '}
                    {Math.round(
                      runbook.similarity *
                        100
                    )}
                    %
                  </span>
                </div>
              )
            )
          ) : (
            <p className="muted">
              No sufficiently relevant runbooks found.
            </p>
          )}
        </div>
      </div>

      <div className="remediation-card">
        <div className="panel-header">
          <div>
            <p className="section-label">
              Remediation Plan
            </p>

            <h3>
              Priority:{' '}
              {
                remediation.priority ||
                '—'
              }
            </h3>
          </div>

          {decision ? (
            <DecisionBadge
              decision={
                decision.decision
              }
            />
          ) : (
            <span className="approval-badge">
              Human approval required
            </span>
          )}
        </div>

        {remediation.status ===
        'withheld_pending_review' ? (
          <div className="remediation-withheld">
            <h4>
              Automated remediation withheld
            </h4>

            <p>
              {remediation.blocked_reason ||
                'The investigation requires human review before remediation actions can be recommended.'}
            </p>

            <p>
              <strong>
                Guardrail decision:
              </strong>{' '}
              {remediation.guardrail_decision ||
                'require_human_review'}
            </p>
          </div>
        ) : (
          <>
            <h4>
              Immediate actions
            </h4>

            <ol>
              {(
                remediation.immediate_actions ||
                []
              ).map((action) => (
                <li key={action}>
                  {action}
                </li>
              ))}
            </ol>

            <h4>
              Follow-up actions
            </h4>

            <ol>
              {(
                remediation.follow_up_actions ||
                []
              ).map((action) => (
                <li key={action}>
                  {action}
                </li>
              ))}
            </ol>
          </>
        )}

        <div className="approval-workflow">
          <div className="approval-heading">
            <div>
              <p className="section-label">
                Human-in-the-Loop
              </p>

              <h3>
                Remediation Decision
              </h3>
            </div>

            <span className="run-reference">
              Agent run #
              {analysis.agent_run_id}
            </span>
          </div>

          {decision ? (
            <div className="decision-summary">
              <DecisionBadge
                decision={
                  decision.decision
                }
              />

              <div>
                <strong>
                  Decision recorded by{' '}
                  {
                    decision.approved_by
                  }
                </strong>

                <p>
                  {decision.notes ||
                    'No reviewer notes provided.'}
                </p>
              </div>
            </div>
          ) : (
            <>
              <div className="approval-form">
                <label>
                  Reviewer
                  <input
                    type="text"
                    value={
                      reviewerName
                    }
                    onChange={(event) =>
                      setReviewerName(
                        event.target.value
                      )
                    }
                    placeholder="Reviewer name"
                  />
                </label>

                <label>
                  Review notes
                  <textarea
                    value={
                      reviewNotes
                    }
                    onChange={(event) =>
                      setReviewNotes(
                        event.target.value
                      )
                    }
                    placeholder="Optional notes about the decision..."
                    rows="3"
                  />
                </label>
              </div>

              <div className="decision-actions">
                <button
                  className="approve-button"
                  onClick={() =>
                    submitDecision(
                      'approved'
                    )
                  }
                  disabled={
                    savingDecision
                  }
                >
                  {savingDecision
                    ? 'Saving...'
                    : 'Approve Remediation'}
                </button>

                <button
                  className="reject-button"
                  onClick={() =>
                    submitDecision(
                      'rejected'
                    )
                  }
                  disabled={
                    savingDecision
                  }
                >
                  Reject Remediation
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default App