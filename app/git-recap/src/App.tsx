import { useState, useEffect, useRef, useCallback } from 'react';
import { Github, Hammer, BookText, Plus, Minus } from 'lucide-react';
import githubIcon from './assets/github-mark-white.png';
import './App.css';

import { Info } from "lucide-react";

import { 
  Button, 
  Card, 
  Input, 
  TextArea, 
  ProgressBar, 
  Accordion, 
  AccordionItem, 
  AccordionTrigger, 
  AccordionContent,
  Popup
} from 'pixel-retroui';

function App() {
  const [pat, setPat] = useState('');
  const [codeHost, setCodeHost] = useState('github');

  // Date states
  const today = new Date().toISOString().split('T')[0];
  const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
  const [startDate, setStartDate] = useState(sevenDaysAgo);
  const [endDate, setEndDate] = useState(today);

  // Filter and output states
  const [showFilters] = useState(false);
  const [availableRepos, setAvailableRepos] = useState<string[]>([]);
  const [selectedRepos, setSelectedRepos] = useState<string[]>([]);
  const [authorInput, setAuthorInput] = useState('');
  const [authors, setAuthors] = useState<string[]>([]);
  const [commitsOutput, setCommitsOutput] = useState('');
  const [dummyOutput, setDummyOutput] = useState('');
  const [progressActions, setProgressActions] = useState(0);
  const [progressWs, setProgressWs] = useState(0);
  const [isExecuting, setIsExecuting] = useState(false);

  // Release Notes states
  const [numOldReleases, setNumOldReleases] = useState(1);
  const [isExecutingReleaseNotes, setIsExecutingReleaseNotes] = useState(false);

  // PR Mode states
  const [showPRMode, setShowPRMode] = useState(false);
  const [availableBranches, setAvailableBranches] = useState<string[]>([]);
  const [sourceBranch, setSourceBranch] = useState('');
  const [targetBranches, setTargetBranches] = useState<string[]>([]);
  const [targetBranch, setTargetBranch] = useState('');
  const [prDiff, setPrDiff] = useState('');
  const [prDescription, setPrDescription] = useState('');
  const [isGeneratingPR, setIsGeneratingPR] = useState(false);
  const [prValidationMessage, setPrValidationMessage] = useState('');
  const [isLoadingBranches, setIsLoadingBranches] = useState(false);
  const [isLoadingTargets, setIsLoadingTargets] = useState(false);
  const [isLoadingDiff, setIsLoadingDiff] = useState(false);
  const [isCreatingPR, setIsCreatingPR] = useState(false);
  const [prCreationSuccess, setPrCreationSuccess] = useState(false);
  const [prUrl, setPrUrl] = useState('');

  // Auth states
  const [isPATAuthorized, setIsPATAuthorized] = useState(false);
  const [authProgress, setAuthProgress] = useState(0);
  const [isAuthorizing, setIsAuthorizing] = useState(false);
  const [authError, setAuthError] = useState(false);  
  const [isGithubAuthorized, setIsGithubAuthorized] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const isAuthorized = isGithubAuthorized || isPATAuthorized;
  
  // URL clone states
  const [repoUrl, setRepoUrl] = useState('');
  const [isCloning, setIsCloning] = useState(false);

  // UI states
  const [isPopupOpen, setIsPopupOpen] = useState(false);
  const [popupMessage, setPopupMessage] = useState('');
  const [selectedN, setSelectedN] = useState(5);
  const [recapDone, setRecapDone] = useState(true);
  const [isReposLoading, setIsReposLoading] = useState(true);
  const [repoProgress, setRepoProgress] = useState(0);
  // UI mode for recap/release/pr
  const [showReleaseMode, setShowReleaseMode] = useState(false);

  const actionsLogRef = useRef<HTMLDivElement>(null);
  const summaryLogRef = useRef<HTMLDivElement>(null);
  const textAreaRef = useRef<HTMLTextAreaElement>(null);
  const [currentWebSocket, setCurrentWebSocket] = useState<WebSocket | null>(null);

  const handleCloneRepo = useCallback(async () => {
    if (!repoUrl) return;
    setIsCloning(true);
    try {
      const backendUrl = import.meta.env.VITE_AICORE_API;
      const response = await fetch(`${backendUrl}/clone-repo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: repoUrl })
      });
      
      if (!response.ok) throw new Error('Failed to clone repository');
      
      const data = await response.json();
      setSessionId(data.session_id);
      setIsPATAuthorized(true);
    } catch (error) {
      console.error('Error cloning repository:', error);
      setPopupMessage('Failed to clone repository. Please check the URL and try again.');
      setIsPopupOpen(true);
    } finally {
      setIsCloning(false);
    }
  }, [repoUrl]);

  const handleRepoToggle = (repo: string) => {
    if (selectedRepos.includes(repo)) {
      setSelectedRepos(selectedRepos.filter((r) => r !== repo));
    } else {
      setSelectedRepos([...selectedRepos, repo]);
    }
  };

  // Fetch available repositories when sessionId changes
  useEffect(() => {
    if (!sessionId) return;
    setIsReposLoading(true);
    setRepoProgress(0);
    const progressInterval = setInterval(() => {
      setRepoProgress((prev) => (prev < 95 ? prev + 5 : prev));
    }, 100);

    const backendUrl = import.meta.env.VITE_AICORE_API;
    fetch(`${backendUrl}/repos?session_id=${sessionId}`)
      .then((response) => response.json())
      .then((data) => {
        setAvailableRepos(data.repos);
        clearInterval(progressInterval);
        setRepoProgress(100);
        setIsReposLoading(false);
      })
      .catch((error) => {
        console.error("Error fetching repos", error);
        clearInterval(progressInterval);
        setRepoProgress(100);
        setIsReposLoading(false);
      });
  }, [sessionId]);

  const addAuthor = () => {
    if (authorInput && !authors.includes(authorInput)) {
      setAuthors([...authors, authorInput]);
      setAuthorInput('');
    }
  };

  const handleFullRecap = () => {
    if (currentWebSocket) {
      currentWebSocket.close();
    }
    setCommitsOutput('');
    setDummyOutput('');
    setProgressActions(0);
    setProgressWs(0);
    setRecapDone(true);
    handleRecap();
  };
  
  const handleNSelection = (n: number) => {
    if (currentWebSocket) {
      currentWebSocket.close();
      setCurrentWebSocket(null);
    }
    setProgressWs(0);
    setDummyOutput('');
    if (commitsOutput) {
      recallWebSocket(commitsOutput, n);
    }
    setSelectedN(n);
  };
  
  const scrollToBottom = () => {
    setTimeout(() => {
      if (textAreaRef.current) {
        textAreaRef.current.scrollTop = textAreaRef.current.scrollHeight;
      }
    }, 0);
  };
  
  const recallWebSocket = (actions: string, n?: number, actionType: string = "recap") => {
    const backendUrl = import.meta.env.VITE_AICORE_API;
    const wsUrl = `${backendUrl.replace(/^http/, 'ws')}/ws/${sessionId}/${actionType}`;
    const ws = new WebSocket(wsUrl);
    
    setCurrentWebSocket(ws);
  
    ws.onopen = () => {
      ws.send(JSON.stringify({ 
        actions, 
        n: n !== undefined ? n : selectedN 
      }));
    };
  
    const progressWsInterval = setInterval(() => {
      setProgressWs((prev) => (prev < 95 ? prev + 5 : prev));
    }, 500);
  
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data.toString()).chunk;
      if (message === "</end>") {
        clearInterval(progressWsInterval);
        setProgressWs(100);
        ws.close();
        setCurrentWebSocket(null);
      } else {
        setDummyOutput((prev) => {
          const newOutput = prev + message;
          scrollToBottom();
          return newOutput;
        });
      }
    };
  
    ws.onerror = (event) => {
      console.error("WebSocket error:", event);
      clearInterval(progressWsInterval);
      setProgressWs(100);
      setCurrentWebSocket(null);
    };
  
    ws.onclose = () => {
      clearInterval(progressWsInterval);
      setCurrentWebSocket(null);
    };
  };
  
  const handleRecap = async () => {
    await fetchInitialActions();
  };

  const handleReleaseNotes = async () => {
    // Validation for GitHub provider
    if (codeHost !== 'github') {
      setPopupMessage('Release Notes generation is only supported for GitHub repositories. Please select GitHub as your provider.');
      setIsPopupOpen(true);
      return;
    }

    // Validation for single repo selection
    if (selectedRepos.length === 0) {
      setPopupMessage('Please select exactly one repository to generate release notes.');
      setIsPopupOpen(true);
      return;
    }

    if (selectedRepos.length > 1) {
      setPopupMessage('Please select only one repository for release notes generation. Multiple repositories are not supported for this feature.');
      setIsPopupOpen(true);
      return;
    }

    if (currentWebSocket) {
      currentWebSocket.close();
    }
    setCommitsOutput('');
    setDummyOutput('');
    setProgressActions(0);
    setProgressWs(0);
    setIsExecutingReleaseNotes(true);
    setRecapDone(false);
    setTimeout(() => {
      actionsLogRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
    await fetchReleaseNotes();
  };

  const fetchReleaseNotes = async () => {
    if (currentWebSocket) {
      currentWebSocket.close();
    }
    setIsExecutingReleaseNotes(true);
    setTimeout(() => {
      actionsLogRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
    const progressReleaseNotesInterval = setInterval(() => {
      setProgressActions((prev) => (prev < 95 ? prev + 1 : prev));
    }, 500);
    try {
      const backendUrl = import.meta.env.VITE_AICORE_API;
      const queryParams = new URLSearchParams({
        session_id: sessionId,
        num_old_releases: numOldReleases.toString(),
        repo_filter: selectedRepos[0]
      }).toString();
      const response = await fetch(`${backendUrl}/release_notes?${queryParams}`, {
        method: 'GET'
      });
      if (!response.ok) throw new Error(`Request failed! Status: ${response.status}`);
      const data = await response.json();
      if (!data.actions) {
        setPopupMessage('Got no actionables for release notes. Please check your repository selection or ensure the repository has releases.');
        setIsPopupOpen(true);
        clearInterval(progressReleaseNotesInterval);
        setProgressActions(100);
        return;
      }
      const mergedOutput = commitsOutput + (commitsOutput ? '\n\n' : '') + data.actions;
      setCommitsOutput(mergedOutput);
      clearInterval(progressReleaseNotesInterval);
      setProgressActions(100);
      summaryLogRef.current?.scrollIntoView({ behavior: 'smooth' });
      recallWebSocket(mergedOutput, undefined, "release");
    } catch (error) {
      console.error('Error during release notes generation:', error);
      setPopupMessage('Error retrieving release notes. Please try again.');
      setIsPopupOpen(true);
    } finally {
      setIsExecutingReleaseNotes(false);
    }
  };
  
  const fetchInitialActions = async () => {
    if (currentWebSocket) {
      currentWebSocket.close();
    }
    setCommitsOutput('');
    setDummyOutput('');
    setProgressActions(0);
    setProgressWs(0);
    setIsExecuting(true);
    setTimeout(() => {
      actionsLogRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
    const progressActionsInterval = setInterval(() => {
      setProgressActions((prev) => (prev < 95 ? prev + 1 : prev));
    }, 500);
    try {
      const backendUrl = import.meta.env.VITE_AICORE_API;
      const queryParams = new URLSearchParams({
        session_id: sessionId,
        start_date: startDate,
        end_date: endDate,
        ...(selectedRepos.length ? { repo_filter: selectedRepos.join(",") } : {}),
        ...(authors.length ? { authors: authors.join(",") } : {}),
      }).toString();
      const response = await fetch(`${backendUrl}/actions?${queryParams}`, {
        method: 'GET'
      });
      if (!response.ok) throw new Error(`Request failed! Status: ${response.status}`);
      const data = await response.json();
      if (!data.actions) {
        setPopupMessage('Got no actionables from Git. Please check your filters or date range. If you are signing with GitHub, you will need to install GitRecap from the Marketplace or authenticate with a PAT instead.');
        setIsPopupOpen(true);
        clearInterval(progressActionsInterval);
        setProgressActions(100);
        return;
      }
      setCommitsOutput(data.actions);
      clearInterval(progressActionsInterval);
      setProgressActions(100);
      summaryLogRef.current?.scrollIntoView({ behavior: 'smooth' });
      recallWebSocket(data.actions);
    } catch (error) {
      console.error('Error during recap:', error);
      setCommitsOutput('Error retrieving actions.');
      setPopupMessage('Error retrieving actions. Please try again.');
      setIsPopupOpen(true);
    } finally {
      setIsExecuting(false);
    }
  };

  // PR Mode Navigation Handlers
  const handleShowPRMode = useCallback(() => {
    // Validation: single repository selection
    if (selectedRepos.length !== 1) {
      setPopupMessage('Please select exactly one repository to create a pull request.');
      setIsPopupOpen(true);
      return;
    }
    
    // Validation: GitHub provider only
    if (codeHost !== 'github') {
      setPopupMessage('Pull request creation is only supported for GitHub repositories.');
      setIsPopupOpen(true);
      return;
    }
    
    // Reset PR mode state
    setSourceBranch('');
    setTargetBranch('');
    setTargetBranches([]);
    setPrDiff('');
    setPrDescription('');
    setPrValidationMessage('');
    setPrCreationSuccess(false);
    setPrUrl('');
    
    setShowPRMode(true);
    
    // Fetch available branches
    fetchAvailableBranches();
  }, [selectedRepos, codeHost, sessionId]);

  const handleBackFromPR = useCallback(() => {
    if (currentWebSocket) {
      currentWebSocket.close();
      setCurrentWebSocket(null);
    }
    setShowPRMode(false);
  }, [currentWebSocket]);

  // Fetch available branches when entering PR mode
  const fetchAvailableBranches = useCallback(async () => {
    if (!sessionId || selectedRepos.length !== 1) return;
    
    setIsLoadingBranches(true);
    setPrValidationMessage('');
    
    try {
      const backendUrl = import.meta.env.VITE_AICORE_API;
      const response = await fetch(
        `${backendUrl}/branches?session_id=${sessionId}&repo=${encodeURIComponent(selectedRepos[0])}`,
        { method: 'GET' }
      );
      
      if (!response.ok) throw new Error('Failed to fetch branches');
      
      const data = await response.json();
      setAvailableBranches(data.branches || []);
      
      if (!data.branches || data.branches.length === 0) {
        setPrValidationMessage('No branches found in this repository.');
      }
    } catch (error) {
      console.error('Error fetching branches:', error);
      setPrValidationMessage('Failed to fetch branches. Please try again.');
    } finally {
      setIsLoadingBranches(false);
    }
  }, [sessionId, selectedRepos]);

  // Handle source branch selection
  const handleSourceBranchChange = useCallback(async (branch: string) => {
    setSourceBranch(branch);
    setTargetBranch('');
    setTargetBranches([]);
    setPrDiff('');
    setPrDescription('');
    setPrValidationMessage('');
    
    if (!branch) return;
    
    // Fetch valid target branches
    setIsLoadingTargets(true);
    
    try {
      const backendUrl = import.meta.env.VITE_AICORE_API;
      const response = await fetch(`${backendUrl}/valid-target-branches`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          repo: selectedRepos[0],
          source_branch: branch
        })
      });
      
      if (!response.ok) throw new Error('Failed to fetch valid target branches');
      
      const data = await response.json();
      setTargetBranches(data.valid_target_branches || []);
      
      if (!data.valid_target_branches || data.valid_target_branches.length === 0) {
        setPrValidationMessage('No valid target branches available for the selected source branch.');
      }
    } catch (error) {
      console.error('Error fetching target branches:', error);
      setPrValidationMessage('Failed to fetch valid target branches. Please try again.');
    } finally {
      setIsLoadingTargets(false);
    }
  }, [sessionId, selectedRepos]);

  // Handle target branch selection and fetch diff
  const handleTargetBranchChange = useCallback(async (branch: string) => {
    setTargetBranch(branch);
    setPrDiff('');
    setPrDescription('');
    setPrValidationMessage('');
    
    if (!branch || !sourceBranch) return;
    
    // Fetch PR diff
    setIsLoadingDiff(true);
    
    try {
      const backendUrl = import.meta.env.VITE_AICORE_API;
      const response = await fetch(`${backendUrl}/get-pull-request-diff`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          repo: selectedRepos[0],
          source_branch: sourceBranch,
          target_branch: branch
        })
      });
      
      if (!response.ok) throw new Error('Failed to fetch pull request diff');
      
      const data = await response.json();
      
      if (!data.commits || data.commits.length === 0) {
        setPrValidationMessage('No changes found between the selected branches.');
        setPrDiff('');
        return;
      }
      
      // Format commits as readable log
      const formattedDiff = data.commits
        .map((commit: any) => `[${commit.sha?.substring(0, 7) || 'N/A'}] ${commit.message}`)
        .join('\n');
      
      setPrDiff(formattedDiff);
    } catch (error) {
      console.error('Error fetching PR diff:', error);
      setPrValidationMessage('Failed to fetch pull request diff. Please try again.');
    } finally {
      setIsLoadingDiff(false);
    }
  }, [sessionId, selectedRepos, sourceBranch]);

  // Generate PR description using WebSocket
  const generatePRDescription = useCallback(() => {
    if (!sourceBranch || !targetBranch || !prDiff) {
      setPrValidationMessage('Please select both branches and ensure there are changes to summarize.');
      return;
    }
    
    if (currentWebSocket) {
      currentWebSocket.close();
    }
    
    setPrDescription('');
    setIsGeneratingPR(true);
    setPrValidationMessage('');
    
    const backendUrl = import.meta.env.VITE_AICORE_API;
    const wsUrl = `${backendUrl.replace(/^http/, 'ws')}/ws/${sessionId}/pull_request`;
    const ws = new WebSocket(wsUrl);
    
    setCurrentWebSocket(ws);
    
    ws.onopen = () => {
      ws.send(JSON.stringify({ actions: prDiff }));
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data.toString()).chunk;
      if (message === "</end>") {
        setIsGeneratingPR(false);
        ws.close();
        setCurrentWebSocket(null);
      } else {
        setPrDescription((prev) => prev + message);
      }
    };
    
    ws.onerror = (event) => {
      console.error("WebSocket error:", event);
      setIsGeneratingPR(false);
      setPrValidationMessage('Failed to generate PR description. Please try again.');
      setCurrentWebSocket(null);
    };
    
    ws.onclose = () => {
      setIsGeneratingPR(false);
      setCurrentWebSocket(null);
    };
  }, [sessionId, sourceBranch, targetBranch, prDiff, currentWebSocket]);

  // Create pull request
  const createPullRequest = useCallback(async () => {
    if (!prDescription || !prDescription.trim()) {
      setPrValidationMessage('Please generate a PR description before creating the pull request.');
      return;
    }
    
    // Parse title from first line of description
    const lines = prDescription.split('\n');
    const title = lines[0]?.replace(/^#+\s*/, '').trim() || `Merge ${sourceBranch} into ${targetBranch}`;
    const body = lines.slice(1).join('\n').trim();
    
    setIsCreatingPR(true);
    setPrValidationMessage('');
    
    try {
      const backendUrl = import.meta.env.VITE_AICORE_API;
      const response = await fetch(`${backendUrl}/create-pull-request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          repo: selectedRepos[0],
          source_branch: sourceBranch,
          target_branch: targetBranch,
          title: title,
          description: body || prDescription
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create pull request');
      }
      
      const data = await response.json();
      
      if (data.success) {
        setPrCreationSuccess(true);
        setPrUrl(data.url);
        setPrValidationMessage('');
      } else {
        throw new Error('Pull request creation was not successful');
      }
    } catch (error: any) {
      console.error('Error creating pull request:', error);
      setPrValidationMessage(error.message || 'Failed to create pull request. Please try again.');
    } finally {
      setIsCreatingPR(false);
    }
  }, [prDescription, sourceBranch, targetBranch, sessionId, selectedRepos]);

  // 1. Add this to your state declarations (around line 60):
  const [showMenu, setShowMenu] = useState(false);

  // 2. Add these handlers after handleShowPRMode (around line 280):
  const handleShowReleaseMode = useCallback(() => {
    setShowMenu(false);
    setShowReleaseMode(true);
    setShowPRMode(false);
  }, []);

  const handleShowPRModeFromMenu = useCallback(() => {
    setShowMenu(false);
    handleShowPRMode();
  }, [handleShowPRMode]);

  // Handle GitHub OAuth callback
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    
    if (!code) return;
    
    const processedCode = sessionStorage.getItem('processedOAuthCode');
    if (processedCode === code) {
      const storedSession = sessionStorage.getItem('githubSessionId');
      if (storedSession) {
        setIsGithubAuthorized(true);
        setSessionId(storedSession);
      }
      return;
    }
  
    sessionStorage.setItem('processedOAuthCode', code);
    
    const backendUrl = import.meta.env.VITE_AICORE_API; 
    const appName = import.meta.env.VITE_APP_NAME;
    const target = `${backendUrl}/external-signup?app=${appName}&accessToken=${code}&provider=GitHub`;
    
    fetch(target, { 
      method: "GET"
    })
      .then(response => response.json())
      .then(data => {
        setIsGithubAuthorized(true);
        setSessionId(data.session_id);
        sessionStorage.setItem('githubSessionId', data.session_id);
        
        if (window.history.replaceState) {
          const newUrl = window.location.pathname + window.location.hash;
          window.history.replaceState(null, '', newUrl);
        }
      })
      .catch(error => {
        console.error("OAuth processing error:", error);
        sessionStorage.removeItem('processedOAuthCode');
      });
  }, []);

  const handleGithubLogin = () => {
    const GITHUB_CLIENT_ID = import.meta.env.VITE_GITHUB_CLIENT_ID;
    const REDIRECT_URI = import.meta.env.VITE_REDIRECT_URI;
    const githubAuthUrl = `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}&redirect_uri=${REDIRECT_URI}&scope=read:user`;
    window.location.href = githubAuthUrl;
  };

  const handlePATAuthorize = async () => {
    const backendUrl = import.meta.env.VITE_AICORE_API;
    setAuthError(false);
    setAuthProgress(0);
    setIsAuthorizing(true);
  
    const progressInterval = setInterval(() => {
      setAuthProgress((prev) => (prev < 90 ? prev + 10 : prev));
    }, 300);
  
    try {
      const response = await fetch(`${backendUrl}/pat`, {
        method: 'POST',
        body: JSON.stringify({
          pat,
          session_id: sessionId,
        })
      });
  
      if (!response.ok) throw new Error('PAT authorization failed.');
  
      const data = await response.json();
      setSessionId(data.session_id);
      setIsPATAuthorized(true);
    } catch (error) {
      console.error('Error authorizing PAT:', error);
      setAuthError(true);
      setPopupMessage("PAT authorization failed. Please check your PAT and try again.");
      setIsPopupOpen(true);
    } finally {
      clearInterval(progressInterval);
      setAuthProgress(100);
      setIsAuthorizing(false);
    }
  };

  return (
    <div className="App">      
      <link rel="icon" type="image/png" href="/favicon.ico"></link>
      <title>GitRecap</title>
      <Card className="app-title p-4 mb-6">
        <h1>Git Recap</h1>
      </Card>      
      <Card className="form-container p-6">
        <div className="github-signin-container mb-6">
          {!isAuthorized ? (
            <>
              <div className="url-clone-container mb-4 flex gap-2 w-full">
                <Input
                  type="text"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="Enter Git repository URL"
                  className="flex-grow min-w-0"
                  style={{ flex: '2 1 0%' }}
                />
                <Button
                  onClick={handleCloneRepo}
                  disabled={isCloning || !repoUrl}
                  color="accent"
                  className="flex-shrink-0"
                  style={{ 
                    width: '33.333%',
                    flex: '1 1 0%',
                    minWidth: 'fit-content'
                  }}
                >
                  {isCloning ? 'Cloning...' : 'Clone'}
                </Button>
              </div>
              <div className="divider mb-4 flex justify-center">
                -- or --
              </div>
              <Button 
                className="github-signin-btn w-full"
                onClick={handleGithubLogin}
                color="accent"
              >
                <img src={githubIcon} alt="GitHub Icon" className="github-icon mr-2" />
                Sign in with GitHub
              </Button>
              
              <Accordion className="mt-4">
                <AccordionItem value="pat-accordion">
                  <AccordionTrigger>
                    or authorize with a PAT
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="form-group pat-group">
                      <div className="mr-4">
                        <label className="block mb-2 font-medium">Personal Access Token (PAT):</label>
                        <Input
                          type={isPATAuthorized ? "password" : "text"}
                          value={pat}
                          onChange={(e) => setPat(e.target.value)}
                          placeholder="Enter your PAT"
                          className={authError ? 'error-input' : ''}
                        />
                      </div>
                      <div>
                        <label className="block mb-2 font-medium">Providers:</label>
                        <div className="flex space-x-2">
                          <Button 
                            onClick={() => setCodeHost('github')}
                            className={`w-full ${codeHost === 'github' ? 'active-btn' : ''} btn-same-height`}
                          >
                            GitHub
                          </Button>
                          <Button 
                            onClick={() => setCodeHost('azure')}
                            className={`w-full ${codeHost === 'azure' ? 'active-btn' : ''} btn-same-height`}
                            disabled={true}
                          >
                            Azure DevOps
                          </Button>
                          <Button 
                            onClick={() => setCodeHost('gitlab')}
                            className={`w-full ${codeHost === 'gitlab' ? 'active-btn' : ''} btn-same-height`}
                            disabled={true}
                          >
                            GitLab
                          </Button>
                        </div>
                      </div>
                    </div>
                    {isAuthorizing && (
                      <ProgressBar
                        progress={authProgress}
                        size="md"
                        color="orange"
                        borderColor="black"
                        className="w-full my-4"
                      />
                    )}
                    <Button 
                      className="authorize-btn mt-4"
                      onClick={handlePATAuthorize}
                      color="accent"
                    >
                      Authorize
                    </Button>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </>
          ) : (
            <Button 
              className="authorized-btn" 
              disabled
              color="dark"
            >
              ✔ Authorized
            </Button>
          )}
        </div>
        
        <div className="form-group date-group mt-6">
          <div className="mr-4">
            <label className="block mb-2 font-medium">Start Date:</label>
            <input 
              type="date" 
              value={startDate} 
              onChange={(e) => setStartDate(e.target.value)} 
              className="retro-input minecraft-font"
            />
          </div>
          <div>
            <label className="block mb-2 font-medium">End Date:</label>
            <input 
              type="date" 
              value={endDate} 
              onChange={(e) => setEndDate(e.target.value)}
              className="retro-input minecraft-font"
            />
          </div>
        </div>

        <Accordion className="mt-6">
          <AccordionItem value="filters-accordion">
            <AccordionTrigger>
              {showFilters ? 'Hide Additional Filters' : 'Show Additional Filters'}
            </AccordionTrigger>
            <AccordionContent>
              <div className="repositories-scroll-container">
                <label className="block mb-2 font-medium flex items-center justify-between">
                  Select Repositories:
                  <div className="group" style={{position: 'relative', display: 'inline-block'}}>
                    <Info className="h-4 w-4 text-gray-500 cursor-pointer" />
                    <div className="tooltip-text">
                      Looking for a repo that is not here? To access private repos,{' '}
                      <a 
                        href="https://docs.github.com/en/apps/using-github-apps/installing-a-github-app-from-github-marketplace-for-your-personal-account" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 underline"
                      >
                        install this App from GitHub Marketplace
                      </a>{' '}
                      or provide a PAT!
                    </div>
                  </div>
                </label>
                {isReposLoading ? (
                  <ProgressBar
                    progress={repoProgress}
                    size="md"
                    color="orange"
                    borderColor="black"
                    className="w-full"
                  />
                ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                  {availableRepos.map((repo) => (
                    <Button
                      key={repo}
                      onClick={() => handleRepoToggle(repo)}
                      className={`grid-button ${selectedRepos.includes(repo) ? 'active-btn' : ''}`}
                    >
                      {repo}
                    </Button>
                  ))}
                </div>
                )}
              </div>
              <div className="authors-section mt-4">
                <div>
                  <label className="block mb-2 font-medium">Add Author:</label>
                  <div className="author-input-group">
                    <Input
                      type="text"
                      value={authorInput}
                      onChange={(e) => setAuthorInput(e.target.value)}
                      placeholder="Enter additional authors to be considered in the actions history"
                      className="author-input-field"
                    />
                    <Button 
                      type="button" 
                      onClick={addAuthor}
                      color="accent"
                      className="author-add-button"
                    >
                      Add
                    </Button>
                  </div>
                </div>
                {authors.length > 0 && (
                  <div className="form-group mt-4">
                    <label className="block mb-2 font-medium">Authors Added:</label>
                    <TextArea 
                      readOnly 
                      value={authors.join(', ')} 
                      rows={2}
                    />
                  </div>
                )}
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </Card>

      <div className={`recap-release-switcher${showReleaseMode ? ' show-release' : ''}${showPRMode ? ' show-pr' : ''}`}>
        {/* Recap Mode */}
        <div className={`recap-main-btn-area${showReleaseMode || showPRMode ? ' slide-left-out' : ' slide-in'}`}>
          <Button
            onClick={handleFullRecap}
            disabled={isExecuting || isExecutingReleaseNotes || !isAuthorized}
            color="accent"
            className="recap-main-btn"
          >
            {isExecuting ? 'Processing...' : 'Recap'}
          </Button>
          <div className="button-with-tooltip">
            <Button
              className="recap-3dots-rect-btn"
              onClick={() => setShowMenu(!showMenu)}
              aria-label="Show options menu"
              disabled={isExecuting || isExecutingReleaseNotes || !isAuthorized}
              type="button"
            >
              <span className="recap-3dots-rect-inner">
                <span className="recap-dot"></span>
                <span className="recap-dot"></span>
                <span className="recap-dot"></span>
              </span>
              <span className="recap-3dots-badge">
                New
              </span>
            </Button>
            <div className="tooltip-text">
              Generate release notes or create a PR - only supported for GitHub repos (requires sign in or PAT authorization)
            </div>
            
            <div className={`options-menu${showMenu ? ' slide-in-menu' : ' slide-out-menu'}`}>
              <Button
                className="menu-option-btn"
                onClick={handleShowReleaseMode}
                disabled={isExecuting || isExecutingReleaseNotes || !isAuthorized || selectedRepos.length !== 1 || codeHost !== 'github'}
                color="accent"
                style={{ minWidth: '180px', maxWidth: '180px' }}
              >
                Generate Release Notes
              </Button>
              <Button
                className="menu-option-btn"
                onClick={handleShowPRModeFromMenu}
                disabled={isExecuting || isExecutingReleaseNotes || !isAuthorized || selectedRepos.length !== 1 || codeHost !== 'github'}
                color="accent"
                style={{ minWidth: '120px', maxWidth: '120px' }}
              >
                Create PR
              </Button>
            </div>
          </div>
        </div>

        {/* Release Notes Mode */}
        <div className={`release-main-btn-area${showReleaseMode && !showPRMode ? ' slide-in' : ' slide-right-out'}`}>
          <Button
            className="release-back-rect-btn"
            onClick={() => setShowReleaseMode(false)}
            disabled={isExecuting || isExecutingReleaseNotes || !isAuthorized}
            type="button"
            style={{ minWidth: '32px', height: '32px' }}
          >
            <span className="release-back-arrow">&#8592;</span>
            <span className="release-back-label">Back</span>
          </Button>
          <Button
            onClick={handleReleaseNotes}
            disabled={isExecutingReleaseNotes || isExecuting || !isAuthorized}
            color="accent"
            className="release-main-btn"
          >
            {isExecutingReleaseNotes ? 'Processing...' : 'Generate Release Notes'}
          </Button>
          <div className="release-counter-rect">
            <button
              onClick={() => setNumOldReleases(Math.max(1, numOldReleases - 1))}
              disabled={numOldReleases <= 1 || isExecutingReleaseNotes || isExecuting}
              className="counter-btn-rect"
              style={{ minWidth: '32px', height: '32px' }}
            >
              <Minus className="h-3 w-3" />
            </button>
            <span className="counter-value-rect">
              {numOldReleases}
            </span>
            <button
              onClick={() => setNumOldReleases(numOldReleases + 1)}
              disabled={isExecutingReleaseNotes || isExecuting}
              className="counter-btn-rect"
              style={{ minWidth: '32px', height: '32px' }}
            >
              <Plus className="h-3 w-3" />
            </button>
          </div>
        </div>
        
        {/* PR Mode */}
        <div className={`pr-main-area${showPRMode ? ' slide-in' : ' slide-right-out'}`}>
          <Button
            className="pr-back-rect-btn"
            onClick={handleBackFromPR}
            disabled={isGeneratingPR || isCreatingPR}
            type="button"
            style={{ minWidth: '90px', height: '44px' }}
          >
            <span className="pr-back-arrow">&#8592;</span>
            <span className="pr-back-label">Back</span>
          </Button>
          
          <div className="pr-controls-container">
            <div className="pr-branch-selectors">
              <div className="pr-branch-group">
                <label className="pr-branch-label">Source Branch:</label>
                <select
                  className="pr-branch-dropdown"
                  value={sourceBranch}
                  onChange={(e) => handleSourceBranchChange(e.target.value)}
                  disabled={isLoadingBranches || isGeneratingPR || isCreatingPR}
                >
                  <option value="">Select source branch</option>
                  {availableBranches.map((branch) => (
                    <option key={branch} value={branch}>
                      {branch}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="pr-branch-group">
                <label className="pr-branch-label">Target Branch:</label>
                <select
                  className="pr-branch-dropdown"
                  value={targetBranch}
                  onChange={(e) => handleTargetBranchChange(e.target.value)}
                  disabled={!sourceBranch || isLoadingTargets || isGeneratingPR || isCreatingPR}
                >
                  <option value="">Select target branch</option>
                  {targetBranches.map((branch) => (
                    <option key={branch} value={branch}>
                      {branch}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            
            {prValidationMessage && (
              <div className="pr-validation-message">
                {prValidationMessage}
              </div>
            )}
            
            <Button
              onClick={generatePRDescription}
              disabled={!sourceBranch || !targetBranch || !prDiff || isGeneratingPR || isCreatingPR}
              color="accent"
              className="pr-generate-btn"
            >
              {isGeneratingPR ? 'Generating...' : 'Generate PR Description'}
            </Button>
          </div>
        </div>
      </div>
      
      {/* PR Mode Output Section */}
      {showPRMode && (
        <>
          <div className="output-section mt-8">
            <Card className="output-box p-6">
              <h2 className="text-xl font-bold mb-4">Commit Diff</h2>
              {isLoadingDiff && (
                <ProgressBar
                  progress={50}
                  size="md"
                  color="orange"
                  borderColor="black"
                  className="w-full mb-4"
                />
              )}
              <TextArea 
                readOnly 
                value={prDiff} 
                rows={10}
                placeholder="Select source and target branches to view commit diff..."
              />
            </Card>
          </div>
          
          <div className="output-section mt-8">
            <Card className="output-box p-6">
              <h2 className="text-xl font-bold mb-4">PR Description</h2>
              {isGeneratingPR && (
                <ProgressBar
                  progress={50}
                  size="md"
                  color="orange"
                  borderColor="black"
                  className="w-full mb-4"
                />
              )}
              <TextArea 
                value={prDescription}
                onChange={(e) => setPrDescription(e.target.value)}
                rows={10}
                placeholder="Click 'Generate PR Description' to create a description..."
              />
              
              {prCreationSuccess && prUrl && (
                <div className="pr-success-message mt-4">
                  Pull request created successfully! <a href={prUrl} target="_blank" rel="noopener noreferrer">View PR</a>
                </div>
              )}
              
              <Button
                onClick={createPullRequest}
                disabled={!prDescription || isGeneratingPR || isCreatingPR}
                color="accent"
                className="pr-create-btn mt-4"
              >
                {isCreatingPR ? 'Creating...' : 'Create PR'}
              </Button>
            </Card>
          </div>
        </>
      )}
      
      <div className="output-section mt-8" ref={actionsLogRef}>
        <Card className="output-box p-6">
          <h2 className="text-xl font-bold mb-4">Actions Log</h2>
          <ProgressBar
            progress={progressActions}
            size="md"
            color="orange"
            borderColor="black"
            className="w-full mb-4"
          />
          <TextArea 
            readOnly 
            value={commitsOutput} 
            rows={10}
          />
        </Card>
      </div>
      <div className="output-section mt-8" ref={summaryLogRef}>
        <Card className="output-box p-6">
          <div className="summary-header">
            <h2>Summary (by `{import.meta.env.VITE_LLM_MODEL}`)</h2>
            <div className="n-selector">
              <Button
                onClick={() => handleNSelection(5)}
                className={`summary-n-btn ${selectedN === 5 ? 'active-btn' : ''}`}
                disabled={!recapDone || isExecutingReleaseNotes || isExecuting}
              >
                5
              </Button>
              <Button
                onClick={() => handleNSelection(10)}
                className={`summary-n-btn ${selectedN === 10 ? 'active-btn' : ''}`}
                disabled={!recapDone || isExecutingReleaseNotes || isExecuting}
              >
                10
              </Button>
              <Button
                onClick={() => handleNSelection(15)}
                className={`summary-n-btn ${selectedN === 15 ? 'active-btn' : ''}`}
                disabled={!recapDone || isExecutingReleaseNotes || isExecuting}
              >
                15
              </Button>
            </div>
          </div>
          <ProgressBar
            progress={progressWs}
            size="md"
            color="orange"
            borderColor="black"
            className="w-full mb-4"
          />
          <TextArea
            readOnly
            value={dummyOutput}
            rows={10}
            ref={textAreaRef}
            style={{
              height: '500px',
              overflowY: 'auto',
              whiteSpace: 'pre-wrap',
              resize: 'none',
              fontFamily: 'monospace'
            }}
          />
        </Card>
      </div>

      <Popup
        isOpen={isPopupOpen}
        onClose={() => setIsPopupOpen(false)}
      >
        <Card className="popup-content p-4">
          <h3 className="text-lg font-bold mb-2">Notification</h3>
          <p>{popupMessage}</p>
          <Button 
            onClick={() => setIsPopupOpen(false)}
            color="accent"
            className="mt-4"
          >
            Close
          </Button>
        </Card>
      </Popup>
      <footer className="footer">
        <div className="footer-content">
          <span>© {new Date().getFullYear()} GitRecap</span>
          <span> | </span>
          <span>License: <a href="https://github.com/BrunoV21/GitRecap/blob/main/LICENSE" target="_blank" rel="noopener noreferrer">Apache 2.0</a></span>
          <span> | </span>
          <a href="https://github.com/BrunoV21/GitRecap" className="footer-link" target="_blank" rel="noopener noreferrer">
            <Github className="h-4 w-4 icon-spacing" />
            Repository
          </a>
          <span> | </span>
          <a href="https://github.com/BrunoV21/GitRecap/wiki" className="footer-link" target="_blank" rel="noopener noreferrer">
            <BookText className="h-4 w-4 icon-spacing" />
            Wiki
          </a>
          <span> | </span>
          <a href="https://github.com/BrunoV21/AiCore" className="footer-link" target="_blank" rel="noopener noreferrer">
            <Hammer className="h-4 w-4 icon-spacing" />
            Built with AiCore
          </a>
        </div>
      </footer>
    </div>
  );
}

export default App;