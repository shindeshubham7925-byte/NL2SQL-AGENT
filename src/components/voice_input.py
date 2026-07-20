# src/components/voice_input.py
"""
Voice Input Component using browser-side Web Speech API.

This component is completely client-side:
1. Renders a mic button using browser-native SpeechRecognition.
2. Directly writes the recognized text to the parent window's Streamlit textarea.
3. Dispatches React input events so Streamlit's state updates automatically.
4. Requires zero Python backend STT processing and no st.rerun().
"""

import streamlit as st
import streamlit.components.v1 as components


def render_voice_input() -> None:
    """
    Renders a fast browser-side speech recognition mic button that updates 
    the text area directly in the browser DOM.
    """
    # HTML and JavaScript code using same-origin access to update the parent textarea
    voice_component_html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: transparent;
    display: flex;
    align-items: center;
    padding: 2px 0;
  }
  .mic-container {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .mic-button {
    width: 42px;
    height: 42px;
    border-radius: 50%;
    border: none;
    cursor: pointer;
    background: #f3f4f6;
    color: #4b5563;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    transition: all 0.2s ease;
    outline: none;
  }
  .mic-button:hover {
    background: #e5e7eb;
    color: #1f2937;
    transform: scale(1.05);
  }
  .mic-button.listening {
    background: #fee2e2;
    color: #ef4444;
    box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.2);
    animation: pulse 1.5s infinite alternate;
  }
  .status-lbl {
    font-size: 13px;
    color: #6b7280;
    font-weight: 500;
  }
  .status-lbl.listening {
    color: #ef4444;
  }
  @keyframes pulse {
    from { transform: scale(1.0); }
    to { transform: scale(1.08); }
  }
  .not-supported {
    font-size: 12px;
    color: #d97706;
    background: #fffbeb;
    padding: 6px 12px;
    border-radius: 6px;
    border: 1px solid #fef3c7;
  }
</style>
</head>
<body>

<div class="mic-container" id="container">
  <!-- Dynamic HTML injected by JS -->
</div>

<script>
(function() {
  const container = document.getElementById('container');
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    container.innerHTML = `<div class="not-supported">⚠️ Browser speech input not supported. Use Chrome or Edge.</div>`;
    return;
  }

  container.innerHTML = `
    <button class="mic-button" id="micBtn" title="Click to speak">🎤</button>
    <span class="status-lbl" id="statusText">Click mic to speak</span>
  `;

  const micBtn = document.getElementById('micBtn');
  const statusText = document.getElementById('statusText');
  let recognition = new SpeechRecognition();
  let isListening = false;

  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = 'en-US';

  recognition.onstart = () => {
    isListening = true;
    micBtn.classList.add('listening');
    micBtn.innerText = '🛑';
    statusText.classList.add('listening');
    statusText.innerText = 'Listening... Speak now';
  };

  recognition.onend = () => {
    isListening = false;
    micBtn.classList.remove('listening');
    micBtn.innerText = '🎤';
    statusText.classList.remove('listening');
    statusText.innerText = 'Click mic to speak';
  };

  recognition.onerror = (event) => {
    console.error('Speech error:', event.error);
    statusText.innerText = 'Error: ' + event.error;
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    if (transcript) {
      try {
        const parentDoc = window.parent.document;
        // Search for Streamlit's textarea elements
        const textArea = parentDoc.querySelector('textarea[data-testid="stTextAreaTextArea"]') || 
                         parentDoc.querySelector('textarea');
        
        if (textArea) {
          // Focus the text area to prepare React state
          textArea.focus();

          // React-safe setter to update the frontend state and trigger change handlers
          const nativeSetter = Object.getOwnPropertyDescriptor(
            window.parent.HTMLTextAreaElement.prototype, 
            'value'
          ).set;
          nativeSetter.call(textArea, transcript);
          
          // Dispatch events to notify React of the change
          textArea.dispatchEvent(new Event('input', { bubbles: true }));
          textArea.dispatchEvent(new Event('change', { bubbles: true }));
          
          // Blur the text area to trigger Streamlit's websocket sync to Python backend
          textArea.blur();
          
          statusText.innerText = 'Speech recognized!';
        } else {
          statusText.innerText = 'Error: Input box not found';
        }
      } catch (e) {
        console.error('Error writing to parent:', e);
        statusText.innerText = 'Permission error writing to input';
      }
    }
  };

  micBtn.addEventListener('click', () => {
    if (isListening) {
      recognition.stop();
    } else {
      recognition.start();
    }
  });
})();
</script>
</body>
</html>
"""
    # Render browser HTML component (height: 50 is enough for mic button + label)
    components.html(voice_component_html, height=52, scrolling=False)
