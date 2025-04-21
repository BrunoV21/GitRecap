
import { useState, useEffect, useRef, useCallback } from 'react';
import { Github, Hammer, BookText } from 'lucide-react';
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
  const [isReposLoading, setIsReposLoading] = useState(true);
  const [repoProgress, setRepoProgress] = useState(0);

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
  
  const recallWebSocket = (actions: string, n?: number) => {
    const backendUrl = import.meta.env.VITE_AICORE_API;
    const wsUrl = `${backendUrl.replace(/^http/, 'ws')}/ws/${sessionId}`;
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
                  className="flex-grow min-w-0"  // Takes remaining space
                  style={{ flex: '2 1 0%' }}     // Explicit 2:1 ratio
                />
                <Button
                  onClick={handleCloneRepo}
                  disabled={isCloning || !repoUrl}
                  color="accent"
                  className="flex-shrink-0"
                  style={{ 
                    width: '33.333%',           // Force 1/3 width
                    flex: '1 1 0%',             // Flex basis 0%
                    minWidth: 'fit-content'     // Prevent squeezing
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
      <div className="recap-button mt-8">
        <Button 
          onClick={handleFullRecap} 
          disabled={isExecuting || !isAuthorized}
          color="accent"
          className="w-full"
        >
          {isExecuting ? 'Processing...' : 'Recap'}
        </Button>
      </div>
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
              <Button onClick={() => handleNSelection(5)} className={`summary-n-btn ${selectedN === 5 ? 'active-btn' : ''}`}>
                5
              </Button>
              <Button onClick={() => handleNSelection(10)} className={`summary-n-btn ${selectedN === 10 ? 'active-btn' : ''}`}>
                10
              </Button>
              <Button onClick={() => handleNSelection(15)} className={`summary-n-btn ${selectedN === 15 ? 'active-btn' : ''}`}>
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