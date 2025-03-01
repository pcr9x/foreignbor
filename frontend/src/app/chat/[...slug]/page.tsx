"use client";

import { useState, useEffect } from "react";
import { use } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface Message {
  id: number;
  message: string;
  sender: string;
  timestamp: string;
  chat_id: string;
}

interface ChatMessagesResponse {
  messages: Message[];
}

export default function ChatPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  // Unwrap the Promise to get the actual params object
  const resolvedParams = use(params);
  const chatId = resolvedParams.slug;

  const [messages, setMessages] = useState<Message[]>([]);
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Function to fetch the messages from the backend
  const fetchMessages = async () => {
    if (!chatId) return;

    setIsLoading(true); // Start loading

    try {
      const response = await fetch(`http://localhost:8000/chat/${chatId}`);
      const data: ChatMessagesResponse = await response.json();

      // Sort messages by ID (ascending order)
      const sortedMessages = [...(data.messages || [])].sort(
        (a, b) => a.id - b.id
      );

      setMessages(sortedMessages);
      console.log("Sorted messages by ID:", sortedMessages);
    } catch (error) {
      console.error("Error fetching chat messages:", error);
    } finally {
      setIsLoading(false); // Stop loading after fetching
    }
  };

  // Fetch messages when the component mounts or when the chatId changes
  useEffect(() => {
    fetchMessages();
  }, [chatId]); // Only re-run when chatId changes

  // Function to handle sending a message
  const handleSendMessage = async () => {
    if (!message.trim()) return;

    try {
      // Looking at your backend, it expects a MessageInput with message and id
      const payload = {
        message: message,
        id: chatId[0], // Make sure this is a string, not undefined
      };

      console.log("Sending payload:", payload); // Debug the payload

      const response = await fetch(`http://localhost:8000/generate-answer`, {
        method: "POST",
        body: JSON.stringify(payload),
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("API error:", errorData);
        throw new Error(
          `Error ${response.status}: ${JSON.stringify(errorData)}`
        );
      }

      const data = await response.json();
      console.log("Response data:", data);

      // Fetch updated messages after sending
      fetchMessages();

      // Clear the message input after sending
      setMessage("");
    } catch (error) {
      console.error("Error sending message:", error);
    }
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Main content area */}
      <div className="flex-1 flex flex-col items-center p-4 bg-gray-100 overflow-hidden">
        <div className="w-full max-w-2xl bg-white shadow-lg rounded-xl p-6 mb-4 flex-1 flex flex-col">
          <h2 className="text-xl font-semibold mb-4">Chat Messages</h2>

          {/* Messages container with scroll */}
          <div className="flex-1 overflow-y-auto mb-4">
            {isLoading ? (
              <div className="flex justify-center items-center h-full">
                <p>Loading messages...</p>
              </div>
            ) : messages.length > 0 ? (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${
                    msg.sender === "user" ? "justify-end" : "justify-start"
                  } mb-2`}
                >
                  <div
                    className={`px-4 py-2 rounded-lg ${
                      msg.sender === "user"
                        ? "bg-blue-500 text-white"
                        : "bg-gray-300"
                    }`}
                  >
                    {msg.message}
                  </div>
                </div>
              ))
            ) : (
              <div className="flex justify-center items-center h-full text-gray-500">
                No messages yet
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Fixed input area at the bottom */}
      <div className="bg-white border-t border-gray-200 p-4">
        <div className="max-w-2xl mx-auto flex items-center gap-4">
          <Textarea
            placeholder="Type your message here."
            className="w-full"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
          />
          <Button
            onClick={handleSendMessage}
            disabled={!message.trim()}
            className="ml-2"
          >
            Send
          </Button>
        </div>
      </div>
    </div>
  );
}