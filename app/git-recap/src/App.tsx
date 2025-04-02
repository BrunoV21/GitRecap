import { useState, useEffect, useRef } from 'react';
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
  // ... existing states ...
  const [pat, setPat] = useState('');
  const [codeHost, setCodeHost] = useState('github');

  // Date states
  const today = new Date().toISOString().split('T')[0];
  const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
  const [startDate, setStartDate] = useState(sevenDaysAgo);
  const [endDate, setEndDate] = useState(today);

  // Accordion and filter states
  const [showFilters] = useState(false);
  const [availableRepos, setAvailableRepos] = useState<string[]>([]);
  const [selectedRepos, setSelectedRepos] = useState<string[]>([]);
  const [authorInput, setAuthorInput] = useState('');
  const [authors, setAuthors] = useState<string[]>([]);

  // Output states
  const [commitsOutput, setCommitsOutput] = useState('');
  const [dummyOutput, setDummyOutput] = useState('');
  // Two separate progress states:
  const [progressActions, setProgressActions] = useState(0);
  const [progressWs, setProgressWs] = useState(0);
  const [isExecuting, setIsExecuting] = useState(false);

  // PAT accordion and authorization states«
  const [isPATAuthorized, setIsPATAuthorized] = useState(false);
  const [authProgress, setAuthProgress] = useState(0);
  const [isAuthorizing, setIsAuthorizing] = useState(false);
  const [authError, setAuthError] = useState(false);  

  // Authorization states for GitHub/session
  const [isGithubAuthorized, setIsGithubAuthorized] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const isAuthorized = isGithubAuthorized || isPATAuthorized;

  // Add popup state
  const [isPopupOpen, setIsPopupOpen] = useState(false);
  const [popupMessage, setPopupMessage] = useState('');

  // Refs for scrolling
  const actionsLogRef = useRef<HTMLDivElement>(null);
  const summaryLogRef = useRef<HTMLDivElement>(null);

  const [selectedN, setSelectedN] = useState(5);

  const handleRepoToggle = (repo: string) => {
    if (selectedRepos.includes(repo)) {
      setSelectedRepos(selectedRepos.filter((r) => r !== repo));
    } else {
      setSelectedRepos([...selectedRepos, repo]);
    }
  };

  const [isReposLoading, setIsReposLoading] = useState(true);
  const [repoProgress, setRepoProgress] = useState(0);

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

  const [currentWebSocket, setCurrentWebSocket] = useState<WebSocket | null>(null);

  const handleFullRecap = () => {
    // Close any existing WebSocket connection
    if (currentWebSocket) {
      currentWebSocket.close();
    }
    
    // Clear current outputs and reset progress
    setCommitsOutput('');
    setDummyOutput('');
    setProgressActions(0);
    setProgressWs(0);
    
    // Force a fresh start
    handleRecap();
  };
  
  const handleNSelection = (n: number) => {
    // Close existing connection immediately
    if (currentWebSocket) {
      currentWebSocket.close();
      setCurrentWebSocket(null);
    }
  
    // Reset state
    setProgressWs(0);
    setDummyOutput('');
    
    // Only proceed if we have commits output
    if (commitsOutput) {
      recallWebSocket(commitsOutput, n);
    }
    
    // Update selectedN
    setSelectedN(n);
  };
  
  const textAreaRef = useRef<HTMLTextAreaElement>(null);
  
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
    
    // Store the current WebSocket reference
    setCurrentWebSocket(ws);
  
    ws.onopen = () => {
      console.log("WebSocket connected with N:", n || selectedN);
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
    // Close any existing WebSocket connection
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
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
  
      if (!response.ok) throw new Error(`Request failed! Status: ${response.status}`);
  
      const data = await response.json();
      
      // Check if actions are empty/falsy
      if (!data.actions) {
        setPopupMessage('Got no actionables from Git. Please check your filters or date range.');
        setIsPopupOpen(true);
        clearInterval(progressActionsInterval);
        setProgressActions(100);
        return; // Exit early since there's nothing to process
      }
      
      setCommitsOutput(data.actions);
      clearInterval(progressActionsInterval);
      setProgressActions(100);
      summaryLogRef.current?.scrollIntoView({ behavior: 'smooth' });
  
      // Now open websocket with the data
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

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    
    if (!code) return;
    
    // Check if we've already processed this specific code
    const processedCode = sessionStorage.getItem('processedOAuthCode');
    if (processedCode === code) {
      console.log("This OAuth code was already processed");
      // Check if we have a stored session from this code
      const storedSession = sessionStorage.getItem('githubSessionId');
      if (storedSession) {
        console.log("Restoring session from storage:", storedSession);
        setIsGithubAuthorized(true);
        setSessionId(storedSession);
      }
      return;
    }
    
    // Store the code we're processing
    sessionStorage.setItem('processedOAuthCode', code);
    
    const backendUrl = import.meta.env.VITE_AICORE_API; 
    const appName = import.meta.env.VITE_APP_NAME;
    const target = `${backendUrl}/external-signup?app=${appName}&accessToken=${code}&provider=GitHub`;
    
    fetch(target, { method: "GET" })
      .then(response => response.json())
      .then(data => {
        console.log("GitHub token response", data);
        setIsGithubAuthorized(true);
        setSessionId(data.session_id);
        
        // Store the session ID in sessionStorage for future use
        sessionStorage.setItem('githubSessionId', data.session_id);
        
        // Clean up the URL after successful processing
        if (window.history.replaceState) {
          const newUrl = window.location.pathname + window.location.hash;
          window.history.replaceState(null, '', newUrl);
        }
      })
      .catch(error => {
        console.error("OAuth processing error:", error);
        // Only remove the stored code on error to allow retry
        sessionStorage.removeItem('processedOAuthCode');
      });
  }, []);

  // Fetch repos using session_id when it is available
  useEffect(() => {
    if (!sessionId) return;
    const backendUrl = import.meta.env.VITE_AICORE_API;
    fetch(`${backendUrl}/repos?session_id=${sessionId}`)
      .then((response) => response.json())
      .then((data) => {
        console.log("Fetched repos:", data.repos);
        setAvailableRepos(data.repos);
      })
      .catch((error) => {
         console.error("Error fetching repos", error);
      });
  }, [sessionId]);

  const handleGithubLogin = () => {
    const GITHUB_CLIENT_ID = import.meta.env.VITE_GITHUB_CLIENT_ID;
    const REDIRECT_URI = import.meta.env.VITE_REDIRECT_URI;
    const githubAuthUrl = `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}&redirect_uri=${REDIRECT_URI}&scope=read:user`;
    window.location.href = githubAuthUrl;
  };

  // Handler for the PAT authorize button remains the same...
  const handlePATAuthorize = async () => {
    const backendUrl = import.meta.env.VITE_AICORE_API;
    setAuthError(false);
    setAuthProgress(0);
    setIsAuthorizing(true);
  
    const progressInterval = setInterval(() => {
      setAuthProgress((prev) => (prev < 90 ? prev + 10 : prev));
    }, 300);
  
    try {
      const payload = {
        pat,
        session_id: sessionId,
      };
  
      const response = await fetch(`${backendUrl}/pat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
  
      if (!response.ok) {
        throw new Error('PAT authorization failed.');
      }
  
      const data = await response.json();
      console.log("PAT stored for session:", data.session_id);
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
              {/* GitHub Signin Button */}
              <Button 
                className="github-signin-btn w-full"  // Added w-full for consistency
                onClick={handleGithubLogin}
                color="accent"   // Changed to accent for the retro look
              >
                <img src={githubIcon} alt="GitHub Icon" className="github-icon mr-2" />
                Sign in with GitHub
              </Button>
              
              {/* PAT Accordion Section */}
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
                            disabled={true} // Or some condition that evaluates to true initially
                          >
                            Azure DevOps
                          </Button>
                          <Button 
                            onClick={() => setCodeHost('gitlab')}
                            className={`w-full ${codeHost === 'gitlab' ? 'active-btn' : ''} btn-same-height`}
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
        
        {/* Date Inputs */}
        <div className="form-group date-group mt-6">
          <div className="mr-4">
            <label className="block mb-2 font-medium">Start Date:</label>
            <input 
              type="date" 
              value={startDate} 
              onChange={(e) => setStartDate(e.target.value)} 
              className="retro-input"
            />
          </div>
          <div>
            <label className="block mb-2 font-medium">End Date:</label>
            <input 
              type="date" 
              value={endDate} 
              onChange={(e) => setEndDate(e.target.value)}
              className="retro-input"
            />
          </div>
        </div>

        {/* Accordion for Additional Filters */}
        <Accordion className="mt-6">
          <AccordionItem value="filters-accordion">
            <AccordionTrigger>
              {showFilters ? 'Hide Additional Filters' : 'Show Additional Filters'}
            </AccordionTrigger>
            <AccordionContent>
              <div className="mb-4">
                <label className="block mb-2 font-medium flex items-center justify-between">
                  Select Repositories:
                  <div className="relative inline-block group">
                    <Info className="h-4 w-4 text-gray-500 cursor-pointer" />
                    <div className="absolute left-1/2 -translate-x-1/2 bottom-6 hidden group-hover:block w-64 bg-beige border border-brown-300 text-brown-800 text-xs rounded-md p-2 shadow-lg z-10 whitespace-normal">
                      Looking for a repo that is not here? To access private repos, install this App from GitHub Marketplace or provide a PAT!
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
                  <div className="grid grid-cols-4 gap-2">
                    {availableRepos.map((repo) => (
                      <Button
                        key={repo}
                        onClick={() => handleRepoToggle(repo)}
                        className={`btn-same-height grid-button ${selectedRepos.includes(repo) ? 'active-btn' : ''}`}
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
                  <div className="author-input-group flex">
                    <Input
                      type="text"
                      value={authorInput}
                      onChange={(e) => setAuthorInput(e.target.value)}
                      placeholder="Enter aditional authors to be considered in the actions history"
                      className="author-input-field mr-2"
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
      {/* Recap Button */}
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
      {/* Output Section */}
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
          {/* Container with title on the left and buttons aligned to the far right */}
          <div className="summary-header relative mb-4">
            {/* Title positioned at the left */}
            <h2 className="text-xl font-bold">
              Summary (as recapped by `{import.meta.env.VITE_LLM_MODEL}`)
            </h2>
            {/* Buttons positioned absolutely to the right edge */}
            <div className="n-selector absolute right-0 top-0 flex space-x-2">
              <Button 
                onClick={() => handleNSelection(5)}
                className={`summary-n-btn ${selectedN === 5 ? 'active-btn' : ''}`}
                disabled={isExecuting || !isAuthorized || selectedN === 5}
              >
                5
              </Button>
              <Button 
                onClick={() => handleNSelection(10)}
                className={`summary-n-btn ${selectedN === 10 ? 'active-btn' : ''}`}
                disabled={isExecuting || !isAuthorized || selectedN === 10}
              >
                10
              </Button>
              <Button 
                onClick={() => handleNSelection(15)}
                className={`summary-n-btn ${selectedN === 15 ? 'active-btn' : ''}`}
                disabled={isExecuting || !isAuthorized || selectedN === 15}
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
              fontFamily: 'monospace' // Optional: for better code display
            }}
          />
        </Card>
      </div>
      {/* Error Popup */}
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
    </div>
  );
}

export default App;