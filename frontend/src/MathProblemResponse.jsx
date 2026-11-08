import { useState, useEffect, useRef } from 'react';
import { createLogger } from './logger.js';

const log = createLogger('answer');

// The answer box. It never sees the solution: `onSubmit(answer)` asks the
// backend to grade the answer and resolves to true (correct), false
// (incorrect), or null (no verdict, e.g. the request failed). The box only
// shows the feedback. `resetKey` changes whenever a new problem loads.
function MathProblemResponse(props) {
    const [response, setResponse] = useState("");
    const [boxColor, setBoxColor] = useState('black');
    const [showIncorrect, setShowIncorrect] = useState(false);
    const [checking, setChecking] = useState(false);
    const inputRef = useRef(null);
    useEffect(() => {
        // Reset the box state whenever a new problem loads.
        setResponse("");
        setBoxColor('black');
        setShowIncorrect(false);
        // Focus the answer box so the user can type right away.
        inputRef.current?.focus();
    }, [props.resetKey]);
    function updateResponse(event) {
        setResponse(event.target.value);
    }
    async function submitResponse() {
        // Ignore blank or whitespace-only submissions; they are neither correct
        // nor incorrect. Also ignore a resubmit while a check is in flight.
        if (response.trim() === "" || checking) {
            return;
        }
        setChecking(true);
        let isCorrect;
        try {
            isCorrect = await props.onSubmit(response);
        } finally {
            setChecking(false);
        }
        if (isCorrect === true) {
            log.debug('Correct answer submitted');
            setResponse("");
            setBoxColor('black');
        } else if (isCorrect === false) {
            log.debug('Incorrect answer submitted');
            setResponse("");
            setBoxColor('red');
            setShowIncorrect(true);
            setTimeout(() => setShowIncorrect(false), 1500);
        }
        // Any other result: no verdict, so the typed answer stays put.
    }
    function inputKeyPress(event){
        if(event.key==="Enter"){
            submitResponse();
        }
    }
    return (
        <div style={{width: '100%', display: 'flex', gap: '8px'}}>
            <input
                ref={inputRef}
                className={`math-problem-input${boxColor === 'red' ? ' incorrect' : ''}`}
                value={response}
                onChange={updateResponse}
                onKeyPress={inputKeyPress}
            />
            <button
                className={`math-problem-submit${showIncorrect ? ' math-problem-submit-incorrect' : ''}`}
                onClick={submitResponse}
                disabled={response.trim() === "" || checking}
            >
                {showIncorrect ? 'Incorrect!' : 'Submit'}
            </button>
        </div>
    );
}

export default MathProblemResponse;
