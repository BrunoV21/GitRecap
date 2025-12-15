typescript
import React, { useState, useEffect, useRef } from 'react';
import { Button, Card, TextArea, Accordion, AccordionItem } from 'pixel-retroui';
import ReactMarkdown from 'react-markdown';
import { toPng } from 'html-to-image';
import { Download, Github, ExternalLink } from 'lucide-react';
import './App.css';

const VITE_AICORE_API = import.meta.env.VITE_AICORE_API || 'http://localhost:7860';
const VITE_GITHUB_CLIENT_ID = import.meta.env.VITE_GITHUB_CLIENT_ID;
const VITE_REDIRECT_URI = import.meta.env.VITE_REDIRECT_URI;
const VITE_LLM_MODEL = import.meta.env.VITE_LLM_MODEL || 'GPT-4';
const VITE_APP_NAME = import.meta.env.VITE_APP_NAME || 'GitRecap';

const STREAM_END_TOKEN = '<|STREAM_END|>';

interface Author {
  name: string;
  email: string;
}

function App() {
  const [sessionId, setSessionId] = useState<string>('');
  const [pat, setPat] = useState<string>('');
  const [provider, setProvider] = useState<string>('GitHub');
  const [repoUrl, setRepoUrl] = useState<string>('');
  const [repos, setRepos] = useState<string[]>([]);
  const [selectedRepos, setSelectedRepos] = useState<string[]>([]);
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [actions, setActions] = useState<string>('');
  const [summary, setSummary] = useState<string>('');
  const [isAuthorized, setIsAuthorized] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [username, setUsername] = useState<string>('');
  const [authMethod, setAuthMethod] = useState<'github' | 'pat' | 'url' | null>(null);
  const [n, setN] = useState<number>(10);
  const [showRelease, setShowRelease] = useState<boolean>(false);
  const [showPR, setShowPR] = useState<boolean>(false);
  const [numOldReleases, setNumOldReleases] = useState<number>(1);
  const [selectedRepoForRelease, setSelectedRepoForRelease] = useState<string>('');
  const [branches, setBranches] = useState<string[]>([]);
  const [sourceBranch, setSourceBranch] = useState<string>('');
  const [targetBranch, setTargetBranch] = useState<string>('');
  const [validTargetBranches, setValidTargetBranches] = useState<string[]>([]);
  const [prDiff, setPrDiff] = useState<string>('');
  const [prDescription, setPrDescription] = useState<string>('');
  const [prUrl, setPrUrl] = useState<string>('');
  const [prError, setPrError] = useState<string>('');
  const [prValidationMessage, setPrValidationMessage] = useState<string>('');
  const [authors, setAuthors] = useState<Author[]>([]);
  const [selectedAuthors, setSelectedAuthors] = useState<string[]>([]);
  const [currentAuthor, setCurrentAuthor] = useState<Author | null>(null);
  const [newAuthorEmail, setNewAuthorEmail] = useState<string>('');
  const [showOptionsMenu, setShowOptionsMenu] = useState<boolean>(false);
  const [showExportModal, setShowExportModal] = useState<boolean>(false);
  const [selectedTheme, setSelectedTheme] = useState<'default' | 'dark' | 'light'>('default');

  const actionsTextareaRef = useRef<HTMLTextAreaElement>(null);
  const summaryTextareaRef = useRef<HTMLTextAreaElement>(null);
  const badgeRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const app = urlParams.get('app');

    if (code && app) {
      handleGitHubCallback(code, app);
    }
  }, []);

  useEffect(() => {
    if (sessionId && isAuthorized) {
      fetchRepos();
      fetchAuthors();
      fetchCurrentAuthor();
    }
  }, [sessionId, isAuthorized]);

  useEffect(() => {
    if (selectedRepoForRelease && showRelease) {
      fetchBranches(selectedRepoForRelease);
    }
  }, [selectedRepoForRelease, showRelease]);

  useEffect(() => {
    if (selectedRepoForRelease && sourceBranch && showPR) {
      fetchValidTargetBranches();
    }
  }, [selectedRepoForRelease, sourceBranch, showPR]);

  const handleGitHubCallback = async (code: string, app: string) => {
    try {
      const response = await fetch(
        `${VITE_AICORE_API}/external-signup?app=${app}&accessToken=${code}&provider=github`
      );
      const data = await response.json();
      setSessionId(data.session_id);
      setIsAuthorized(true);
      setAuthMethod('github');
      setUsername(data.username || 'User');
      window.history.replaceState({}, document.title, window.location.pathname);
    } catch (error) {
      console.error('GitHub authentication failed:', error);
    }
  };

  const handleGitHubSignIn = () => {
    const githubAuthUrl = `https://github.com/login/oauth/authorize?client_id=${VITE_GITHUB_CLIENT_ID}&redirect_uri=${VITE_REDIRECT_URI}&scope=repo&state=${VITE_APP_NAME}`;
    window.location.href = githubAuthUrl;
  };

  const handlePATSubmit = async () => {
    if (!pat.trim()) return;

    try {
      const response = await fetch(`${VITE_AICORE_API}/pat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pat, provider }),
      });
      const data = await response.json();
      setSessionId(data.session_id);
      setIsAuthorized(true);
      setAuthMethod('pat');
      setUsername(data.username || 'User');
    } catch (error) {
      console.error('PAT authentication failed:', error);
    }
  };

  const handleURLSubmit = async () => {
    if (!repoUrl.trim()) return;

    try {
      const response = await fetch(`${VITE_AICORE_API}/clone-repo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: repoUrl }),
      });
      const data = await response.json();
      setSessionId(data.session_id);
      setIsAuthorized(true);
      setAuthMethod('url');
      setUsername('URL User');
    } catch (error) {
      console.error('URL clone failed:', error);
    }
  };

  const fetchRepos = async () => {
    try {
      const response = await fetch(`${VITE_AICORE_API}/repos?session_id=${sessionId}`);
      const data = await response.json();
      setRepos(data.repos || []);
    } catch (error) {
      console.error('Failed to fetch repos:', error);
    }
  };

  const fetchAuthors = async () => {
    try {
      const response = await fetch(`${VITE_AICORE_API}/api/authors`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, repo_names: [] }),
      });
      const data = await response.json();
      setAuthors(data.authors || []);
    } catch (error) {
      console.error('Failed to fetch authors:', error);
    }
  };

  const fetchCurrentAuthor = async () => {
    try {
      const response = await fetch(`${VITE_AICORE_API}/api/current-author?session_id=${sessionId}`);
      const data = await response.json();
      if (data.author) {
        setCurrentAuthor(data.author);
        setSelectedAuthors([data.author.email]);
      }
    } catch (error) {
      console.error('Failed to fetch current author:', error);
    }
  };

  const fetchBranches = async (repo: string) => {
    try {
      const response = await fetch(`${VITE_AICORE_API}/branches?session_id=${sessionId}&repo=${encodeURIComponent(repo)}`);
      const data = await response.json();
      setBranches(data.branches || []);
    } catch (error) {
      console.error('Failed to fetch branches:', error);
    }
  };

  const fetchValidTargetBranches = async () => {
    try {
      const response = await fetch(`${VITE_AICORE_API}/valid-target-branches`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          repo: selectedRepoForRelease,
          source_branch: sourceBranch,
        }),
      });
      const data = await response.json();
      setValidTargetBranches(data.valid_target_branches || []);
    } catch (error) {
      console.error('Failed to fetch valid target branches:', error);
    }
  };

  const handleRepoToggle = (repo: string) => {
    setSelectedRepos((prev) =>
      prev.includes(repo) ? prev.filter((r) => r !== repo) : [...prev, repo]
    );
  };

  const handleAuthorToggle = (email: string) => {
    setSelectedAuthors((prev) =>
      prev.includes(email) ? prev.filter((e) => e !== email) : [...prev, email]
    );
  };

  const handleAddAuthor = () => {
    if (newAuthorEmail.trim() && !selectedAuthors.includes(newAuthorEmail.trim())) {
      setSelectedAuthors((prev) => [...prev, newAuthorEmail.trim()]);
      setNewAuthorEmail('');
    }
  };

  const handleFetchActions = async () => {
    if (!sessionId) return;

    try {
      const params = new URLSearchParams({
        session_id: sessionId,
        ...(startDate && { start_date: new Date(startDate).toISOString() }),
        ...(endDate && { end_date: new Date(endDate).toISOString() }),
      });

      if (selectedRepos.length > 0) {
        selectedRepos.forEach((repo) => params.append('repo_filter', repo));
      }

      if (selectedAuthors.length > 0) {
        selectedAuthors.forEach((author) => params.append('authors', author));
      }

      const response = await fetch(`${VITE_AICORE_API}/actions?${params.toString()}`);
      const data = await response.json();
      setActions(data.actions || '');
      scrollToBottom(actionsTextareaRef);
    } catch (error) {
      console.error('Failed to fetch actions:', error);
    }
  };

  const handleRecap = async () => {
    if (!sessionId || !actions) return;

    setIsLoading(true);
    setSummary('');

    try {
      const ws = new WebSocket(`${VITE_AICORE_API.replace('http', 'ws')}/ws`);

      ws.onopen = () => {
        ws.send(
          JSON.stringify({
            session_id: sessionId,
            action: 'recap',
            message: actions,
            n,
          })
        );
      };

      ws.onmessage = (event) => {
        const chunk = event.data;
        if (chunk === STREAM_END_TOKEN) {
          ws.close();
          setIsLoading(false);
        } else {
          setSummary((prev) => prev + chunk);
          scrollToBottom(summaryTextareaRef);
        }
      };

      ws.onerror = () => {
        setIsLoading(false);
        ws.close();
      };
    } catch (error) {
      console.error('Recap failed:', error);
      setIsLoading(false);
    }
  };

  const handleRelease = async () => {
    if (!sessionId || !selectedRepoForRelease) return;

    setIsLoading(true);
    setSummary('');

    try {
      const params = new URLSearchParams({
        session_id: sessionId,
        num_old_releases: numOldReleases.toString(),
      });
      params.append('repo_filter', selectedRepoForRelease);

      const response = await fetch(`${VITE_AICORE_API}/release_notes?${params.toString()}`);
      const data = await response.json();
      const releaseActions = data.actions || '';

      const ws = new WebSocket(`${VITE_AICORE_API.replace('http', 'ws')}/ws`);

      ws.onopen = () => {
        ws.send(
          JSON.stringify({
            session_id: sessionId,
            action: 'release',
            message: releaseActions,
          })
        );
      };

      ws.onmessage = (event) => {
        const chunk = event.data;
        if (chunk === STREAM_END_TOKEN) {
          ws.close();
          setIsLoading(false);
        } else {
          setSummary((prev) => prev + chunk);
          scrollToBottom(summaryTextareaRef);
        }
      };

      ws.onerror = () => {
        setIsLoading(false);
        ws.close();
      };
    } catch (error) {
      console.error('Release notes generation failed:', error);
      setIsLoading(false);
    }
  };

  const handleGeneratePRDescription = async () => {
    if (!sessionId || !selectedRepoForRelease || !sourceBranch || !targetBranch) return;

    setIsLoading(true);
    setPrDescription('');
    setPrError('');
    setPrValidationMessage('');

    try {
      const response = await fetch(`${VITE_AICORE_API}/get-pull-request-diff`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          repo: selectedRepoForRelease,
          source_branch: sourceBranch,
          target_branch: targetBranch,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        setPrError(errorData.detail || 'Failed to fetch PR diff');
        setIsLoading(false);
        return;
      }

      const data = await response.json();
      const diffActions = data.actions || '';
      setPrDiff(diffActions);

      const ws = new WebSocket(`${VITE_AICORE_API.replace('http', 'ws')}/ws`);

      ws.onopen = () => {
        ws.send(
          JSON.stringify({
            session_id: sessionId,
            action: 'pull_request',
            message: diffActions,
          })
        );
      };

      ws.onmessage = (event) => {
        const chunk = event.data;
        if (chunk === STREAM_END_TOKEN) {
          ws.close();
          setIsLoading(false);
        } else {
          setPrDescription((prev) => prev + chunk);
        }
      };

      ws.onerror = () => {
        setIsLoading(false);
        ws.close();
      };
    } catch (error) {
      console.error('PR description generation failed:', error);
      setPrError('Failed to generate PR description');
      setIsLoading(false);
    }
  };

  const handleCreatePR = async () => {
    if (!sessionId || !selectedRepoForRelease || !sourceBranch || !targetBranch || !prDescription) return;

    setIsLoading(true);
    setPrError('');
    setPrUrl('');

    try {
      const response = await fetch(`${VITE_AICORE_API}/create-pull-request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          repo: selectedRepoForRelease,
          source_branch: sourceBranch,
          target_branch: targetBranch,
          body: prDescription,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        setPrError(errorData.detail || 'Failed to create pull request');
        setIsLoading(false);
        return;
      }

      const data = await response.json();
      if (data.success && data.url) {
        setPrUrl(data.url);
      } else {
        setPrError('Pull request creation failed');
      }
      setIsLoading(false);
    } catch (error) {
      console.error('PR creation failed:', error);
      setPrError('Failed to create pull request');
      setIsLoading(false);
    }
  };

  const scrollToBottom = (ref: React.RefObject<HTMLTextAreaElement>) => {
    if (ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight;
    }
  };

  const handleNSelection = (newN: number) => {
    setN(newN);
    if (actions) {
      handleRecap();
    }
  };

  const handleSwitchToRelease = () => {
    setShowRelease(true);
    setShowPR(false);
    setShowOptionsMenu(false);
  };

  const handleSwitchToPR = () => {
    setShowPR(true);
    setShowRelease(false);
    setShowOptionsMenu(false);
  };

  const handleBackToRecap = () => {
    setShowRelease(false);
    setShowPR(false);
    setShowOptionsMenu(false);
  };

  const handleExportPNG = async () => {
    if (!badgeRef.current) return;

    try {
      const dataUrl = await toPng(badgeRef.current, {
        quality: 1.0,
        pixelRatio: 2,
      });
      const link = document.createElement('a');
      link.download = 'gitrecap-badge.png';
      link.href = dataUrl;
      link.click();
      setShowExportModal(false);
    } catch (error) {
      console.error('Failed to export PNG:', error);
    }
  };

  const handleExportHTML = () => {
    if (!badgeRef.current) return;

    const badgeHTML = badgeRef.current.outerHTML;
    const fullHTML = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GitRecap Badge</title>
  <style>
    ${document.querySelector('style')?.textContent || ''}
  </style>
</head>
<body>
  ${badgeHTML}
</body>
</html>
    `;

    const blob = new Blob([fullHTML], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.download = 'gitrecap-badge.html';
    link.href = url;
    link.click();
    URL.revokeObjectURL(url);
    setShowExportModal(false);
  };

  const generateBadgeContent = (theme: 'default' | 'dark' | 'light') => {
    return {
      theme,
      title: 'GitRecap',
      summary: summary || 'No summary generated yet',
      username: username || 'User',
      repos: selectedRepos.join(', ') || 'All repositories',
      dateRange: startDate && endDate ? `${startDate} to ${endDate}` : 'All time',
    };
  };

  return (
    <div className="App">
      <h1>GitRecap</h1>

      {!isAuthorized ? (
        <Card className="form-container">
          <h2>Authorize Access</h2>
          <div className="form-group">
            <button className="github-signin-btn w-full" onClick={handleGitHubSignIn}>
              <Github className="github-icon" />
              Sign in with GitHub
            </button>
          </div>

          <div className="form-group">
            <h3>Or use Personal Access Token</h3>
            <div className="pat-group">
              <div>
                <label>Provider</label>
                <select value={provider} onChange={(e) => setProvider(e.target.value)}>
                  <option value="GitHub">GitHub</option>
                  <option value="GitLab">GitLab</option>
                  <option value="Azure">Azure DevOps</option>
                </select>
              </div>
              <div>
                <label>Personal Access Token</label>
                <input
                  type="password"
                  value={pat}
                  onChange={(e) => setPat(e.target.value)}
                  placeholder="Enter your PAT"
                />
              </div>
              <button onClick={handlePATSubmit}>Authorize</button>
            </div>
          </div>

          <div className="form-group">
            <h3>Or clone from URL</h3>
            <label>Repository URL</label>
            <input
              type="text"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/user/repo"
            />
            <button className="mt-4" onClick={handleURLSubmit}>
              Clone Repository
            </button>
          </div>
        </Card>
      ) : (
        <>
          <Card className="form-container">
            <h2>Filters</h2>
            <Accordion>
              <AccordionItem title="Date Range">
                <div className="date-group">
                  <div>
                    <label>Start Date</label>
                    <input
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                    />
                  </div>
                  <div>
                    <label>End Date</label>
                    <input
                      type="date"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                    />
                  </div>
                </div>
              </AccordionItem>

              <AccordionItem title="Repositories">
                <div className="repositories-scroll-container">
                  <div className="grid">
                    {repos.map((repo) => (
                      <Button
                        key={repo}
                        className={`grid-button ${selectedRepos.includes(repo) ? 'active-btn' : ''}`}
                        onClick={() => handleRepoToggle(repo)}
                      >
                        {repo}
                      </Button>
                    ))}
                  </div>
                </div>

                <div className="authors-section">
                  <h3>Filter by Authors</h3>
                  <div className="grid">
                    {authors.map((author) => (
                      <Button
                        key={author.email}
                        className={`grid-button ${selectedAuthors.includes(author.email) ? 'active-btn' : ''}`}
                        onClick={() => handleAuthorToggle(author.email)}
                        title={`${author.name} (${author.email})`}
                      >
                        {author.name}
                      </Button>
                    ))}
                  </div>

                  <div className="author-input-container mt-4">
                    <div className="author-input-group">
                      <input
                        type="email"
                        className="author-input-field"
                        value={newAuthorEmail}
                        onChange={(e) => setNewAuthorEmail(e.target.value)}
                        placeholder="Add author email"
                      />
                      <Button className="author-add-button" onClick={handleAddAuthor}>
                        Add
                      </Button>
                    </div>
                  </div>
                </div>
              </AccordionItem>
            </Accordion>

            <Button className="mt-4 w-full" onClick={handleFetchActions}>
              Fetch Actions
            </Button>
          </Card>

          <div className="recap-release-switcher-container">
            <div className={`recap-release-switcher ${showRelease ? 'show-release' : ''} ${showPR ? 'show-pr' : ''}`}>
              <div className={`recap-main-btn-area ${!showRelease && !showPR ? 'slide-in' : 'slide-left-out'}`}>
                <Button
                  className="recap-main-btn retro-btn"
                  onClick={handleRecap}
                  disabled={!actions || isLoading}
                >
                  {isLoading ? 'Generating...' : 'Generate Recap'}
                </Button>

                <div className="button-with-tooltip">
                  <Button
                    className="recap-3dots-rect-btn retro-btn"
                    onClick={() => setShowOptionsMenu(!showOptionsMenu)}
                    disabled={!selectedRepoForRelease}
                  >
                    <div className="recap-3dots-rect-inner">
                      <div className="recap-dot"></div>
                      <div className="recap-dot"></div>
                      <div className="recap-dot"></div>
                    </div>
                  </Button>
                  {!selectedRepoForRelease && (
                    <div className="tooltip-text">
                      Please select exactly one repository from the filters above to enable Release Notes and Pull Request features.
                    </div>
                  )}
                  {selectedRepoForRelease && (
                    <span className="recap-3dots-badge">1</span>
                  )}

                  <div className={`options-menu ${showOptionsMenu ? 'slide-in-menu' : 'slide-out-menu'}`}>
                    <div className="menu-button-with-tooltip">
                      <Button
                        className="menu-option-btn retro-btn"
                        onClick={handleSwitchToRelease}
                        disabled={!selectedRepoForRelease || authMethod === 'url'}
                      >
                        Release Notes
                      </Button>
                      {authMethod === 'url' && (
                        <div className="menu-tooltip-text">
                          Release notes are not available for URL-cloned repositories
                        </div>
                      )}
                    </div>

                    <div className="menu-button-with-tooltip">
                      <Button
                        className="menu-option-btn retro-btn"
                        onClick={handleSwitchToPR}
                        disabled={!selectedRepoForRelease || authMethod !== 'github'}
                      >
                        Pull Request
                      </Button>
                      {authMethod !== 'github' && (
                        <div className="menu-tooltip-text">
                          Pull requests require GitHub authentication. Please sign in with GitHub to use this feature.
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              <div className={`release-main-btn-area ${showRelease && !showPR ? 'slide-in' : 'slide-right-out'}`}>
                <Button className="release-back-rect-btn retro-btn" onClick={handleBackToRecap}>
                  <span className="release-back-arrow">←</span> Back
                </Button>

                <Button
                  className="release-main-btn retro-btn"
                  onClick={handleRelease}
                  disabled={!selectedRepoForRelease || isLoading}
                >
                  {isLoading ? 'Generating...' : 'Generate Release Notes'}
                </Button>

                <div className="release-counter-rect">
                  <Button
                    className="counter-btn-rect"
                    onClick={() => setNumOldReleases(Math.max(1, numOldReleases - 1))}
                    disabled={numOldReleases <= 1}
                  >
                    -
                  </Button>
                  <span className="counter-value-rect">{numOldReleases}</span>
                  <Button
                    className="counter-btn-rect"
                    onClick={() => setNumOldReleases(numOldReleases + 1)}
                  >
                    +
                  </Button>
                </div>
              </div>

              <div className={`pr-main-area ${showPR ? 'slide-in' : 'slide-right-out'}`}>
                <Button className="pr-back-rect-btn retro-btn" onClick={handleBackToRecap}>
                  <span className="pr-back-arrow">←</span> Back
                </Button>

                <div className="pr-branch-group-inline">
                  <label className="pr-branch-label">From:</label>
                  <select
                    className="pr-branch-dropdown"
                    value={sourceBranch}
                    onChange={(e) => setSourceBranch(e.target.value)}
                    disabled={!selectedRepoForRelease}
                  >
                    <option value="">Select branch</option>
                    {branches.map((branch) => (
                      <option key={branch} value={branch}>
                        {branch}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="pr-branch-group-inline">
                  <label className="pr-branch-label">To:</label>
                  <select
                    className="pr-branch-dropdown"
                    value={targetBranch}
                    onChange={(e) => setTargetBranch(e.target.value)}
                    disabled={!sourceBranch || validTargetBranches.length === 0}
                  >
                    <option value="">Select branch</option>
                    {validTargetBranches.map((branch) => (
                      <option key={branch} value={branch}>
                        {branch}
                      </option>
                    ))}
                  </select>
                </div>

                <Button
                  className="pr-generate-btn retro-btn"
                  onClick={handleGeneratePRDescription}
                  disabled={!sourceBranch || !targetBranch || isLoading}
                >
                  {isLoading ? 'Generating...' : 'Generate Description'}
                </Button>

                {prValidationMessage && (
                  <div className="pr-validation-message-inline">{prValidationMessage}</div>
                )}
              </div>
            </div>
          </div>

          <div className="output-section">
            <div className="output-box">
              <h2>Actions</h2>
              <TextArea
                ref={actionsTextareaRef}
                value={actions}
                onChange={(e) => setActions(e.target.value)}
                placeholder="Git actions will appear here..."
                readOnly
              />
            </div>

            <div className="output-box">
              <div className="summary-header">
                <h2>Summary</h2>
                {!showRelease && !showPR && (
                  <div className="n-selector">
                    {[5, 10, 15].map((value) => (
                      <Button
                        key={value}
                        className={`summary-n-btn ${n === value ? 'active-btn' : ''}`}
                        onClick={() => handleNSelection(value)}
                      >
                        {value}
                      </Button>
                    ))}
                  </div>
                )}
              </div>
              {showPR ? (
                <>
                  <TextArea
                    value={prDescription}
                    onChange={(e) => setPrDescription(e.target.value)}
                    placeholder="PR description will appear here..."
                  />
                  {prError && <div className="pr-error-message mt-4">{prError}</div>}
                  {prUrl && (
                    <div className="pr-success-message mt-4">
                      Pull request created successfully!{' '}
                      <a href={prUrl} target="_blank" rel="noopener noreferrer">
                        View PR <ExternalLink size={14} style={{ display: 'inline' }} />
                      </a>
                    </div>
                  )}
                  {authMethod === 'github' && prDescription && !prUrl && (
                    <div className="pr-creation-section">
                      <Button
                        className="pr-create-btn retro-btn mt-4"
                        onClick={handleCreatePR}
                        disabled={isLoading}
                      >
                        {isLoading ? 'Creating...' : 'Create Pull Request'}
                      </Button>
                    </div>
                  )}
                  {authMethod !== 'github' && (
                    <div className="pr-auth-message mt-4">
                      Pull request creation requires GitHub authentication. Please sign in with GitHub to create pull requests.
                    </div>
                  )}
                </>
              ) : (
                <TextArea
                  ref={summaryTextareaRef}
                  value={summary}
                  onChange={(e) => setSummary(e.target.value)}
                  placeholder="Summary will appear here..."
                  readOnly
                />
              )}
            </div>
          </div>

          {summary && !showPR && (
            <div className="export-button-container">
              <button className="export-button" onClick={() => setShowExportModal(true)}>
                <Download className="export-icon" />
                Export Badge
              </button>
            </div>
          )}

          {showExportModal && (
            <div className="export-modal-overlay" onClick={() => setShowExportModal(false)}>
              <div className="export-modal" onClick={(e) => e.stopPropagation()}>
                <h2>Export GitRecap Badge</h2>

                <div className="theme-selector">
                  <label>Select Theme:</label>
                  <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                    {(['default', 'dark', 'light'] as const).map((theme) => (
                      <button
                        key={theme}
                        className={`theme-option ${selectedTheme === theme ? 'active' : ''}`}
                        onClick={() => setSelectedTheme(theme)}
                      >
                        {theme.charAt(0).toUpperCase() + theme.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="export-options">
                  <button className="export-option-btn" onClick={handleExportPNG}>
                    <span className="option-icon">🖼️</span>
                    <span className="option-title">Export as PNG</span>
                    <span className="option-desc">Download as image file</span>
                  </button>

                  <button className="export-option-btn" onClick={handleExportHTML}>
                    <span className="option-icon">📄</span>
                    <span className="option-title">Export as HTML</span>
                    <span className="option-desc">Download as standalone HTML</span>
                  </button>
                </div>

                <button className="close-modal-btn" onClick={() => setShowExportModal(false)}>
                  Close
                </button>
              </div>
            </div>
          )}

          <div className="badge-preview" ref={badgeRef}>
            <div className={`gitrecap-badge theme-${selectedTheme}`}>
              <div className="badge-header">
                <div className="badge-logo">
                  <img src="/favicon.ico" alt="GitRecap" style={{ width: '100%', height: '100%' }} />
                </div>
                <div className="badge-title">GitRecap</div>
                <div className="badge-meta-header">
                  <strong>User:</strong> {username}<br />
                  <strong>Repos:</strong> {selectedRepos.length > 0 ? selectedRepos.join(', ') : 'All'}<br />
                  <strong>Period:</strong> {startDate && endDate ? `${startDate} to ${endDate}` : 'All time'}
                </div>
              </div>
              <div className="badge-content">
                <div className="badge-summary">
                  <ReactMarkdown>{summary}</ReactMarkdown>
                </div>
              </div>
              <div className="badge-footer">
                Generated by <a href="https://brunov21.github.io/GitRecap/" target="_blank" rel="noopener noreferrer">GitRecap</a> • Powered by {VITE_LLM_MODEL}
              </div>
            </div>
          </div>
        </>
      )}

      <footer className="footer">
        <div className="footer-content">
          <span>Made with ❤️ by</span>
          <a
            href="https://github.com/BrunoV21"
            target="_blank"
            rel="noopener noreferrer"
            className="footer-link"
          >
            <Github size={16} className="icon-spacing" />
            BrunoV21
          </a>
        </div>
      </footer>
    </div>
  );
}

export default App;