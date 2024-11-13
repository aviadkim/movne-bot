<?php
/*
Plugin Name: Movne Chat Widget
Description: Integrates Movne chatbot with WordPress
Version: 1.0
Author: Movne Global
*/

// Prevent direct access to this file
if (!defined('ABSPATH')) {
    exit;
}

// Add the chat widget HTML and JavaScript
function movne_chat_widget_code() {
    $railway_url = 'YOUR_RAILWAY_URL'; // Replace with your Railway app URL once deployed
    ?>
    <style>
        #movne-chat-widget {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 350px;
            height: 500px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            display: none;
            flex-direction: column;
            z-index: 1000;
            direction: rtl;
        }
        #movne-chat-header {
            padding: 15px;
            background: #007bff;
            color: white;
            border-radius: 10px 10px 0 0;
            font-weight: bold;
        }
        #movne-chat-messages {
            flex-grow: 1;
            overflow-y: auto;
            padding: 15px;
        }
        #movne-chat-input {
            padding: 15px;
            border-top: 1px solid #eee;
        }
        #movne-chat-input input {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            direction: rtl;
        }
        #movne-chat-button {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 60px;
            height: 60px;
            background: #007bff;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 1000;
        }
        .message {
            margin-bottom: 10px;
            padding: 8px;
            border-radius: 5px;
            max-width: 80%;
        }
        .user-message {
            background: #e9ecef;
            margin-left: auto;
        }
        .bot-message {
            background: #f8f9fa;
            margin-right: auto;
        }
    </style>

    <div id="movne-chat-button">💬</div>
    <div id="movne-chat-widget">
        <div id="movne-chat-header">מובנה גלובל - שיווק השקעות</div>
        <div id="movne-chat-messages"></div>
        <div id="movne-chat-input">
            <input type="text" placeholder="איך אוכל לעזור לך היום?" />
        </div>
    </div>

    <script>
    document.addEventListener('DOMContentLoaded', function() {
        let conversationId = null;
        const chatButton = document.getElementById('movne-chat-button');
        const chatWidget = document.getElementById('movne-chat-widget');
        const messagesContainer = document.getElementById('movne-chat-messages');
        const chatInput = document.querySelector('#movne-chat-input input');

        chatButton.addEventListener('click', function() {
            if (chatWidget.style.display === 'none' || !chatWidget.style.display) {
                chatWidget.style.display = 'flex';
                chatButton.style.display = 'none';
            }
        });

        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && chatInput.value.trim()) {
                const message = chatInput.value.trim();
                addMessage(message, 'user');
                sendMessage(message);
                chatInput.value = '';
            }
        });

        function addMessage(message, sender) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            messageDiv.textContent = message;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        async function sendMessage(message) {
            try {
                const response = await fetch('<?php echo $railway_url; ?>/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        conversation_id: conversationId
                    })
                });

                const data = await response.json();
                conversationId = data.conversation_id;
                addMessage(data.response, 'bot');
            } catch (error) {
                console.error('Error:', error);
                addMessage('מצטער, אירעה שגיאה. אנא נסה שוב.', 'bot');
            }
        }
    });
    </script>
    <?php
}

// Add the widget code to the footer
add_action('wp_footer', 'movne_chat_widget_code');
