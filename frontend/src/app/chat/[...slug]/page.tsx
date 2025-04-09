"use client";

import { use, useState, useEffect, useRef } from "react";
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

export default function Page({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);
  const chatId = slug[0];

  const [messages, setMessages] = useState<Message[]>([]);
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isSending, setIsSending] = useState<boolean>(false);

  // Create a ref to the messages container
  const messagesContainerRef = useRef<HTMLDivElement>(null);

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

  // Scroll to the bottom of the messages container after messages change
  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop =
        messagesContainerRef.current.scrollHeight;
    }
  }, [messages]);

  // Function to handle sending a message
  const handleSendMessage = async () => {
    if (!message.trim() || isSending) return;

    setIsSending(true);

    try {
      // Send the message to the backend
      const payload = {
        message: message,
        id: chatId, // Make sure this is a string, not undefined
      };

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

      // Clear the message input after sending
      setMessage("");

      // Fetch updated messages to show the new conversation
      await fetchMessages();
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
      setIsSending(false);
    }
  };

  // Format the message content with proper line breaks
  const formatMessage = (content: string) => {
    return content.split("\n").map((line, i) => (
      <span key={i}>
        {line}
        {i < content.split("\n").length - 1 && <br />}
      </span>
    ));
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Main content area */}
      <div className="flex-1 flex flex-col items-center p-4 bg-gray-100 overflow-hidden">
        <div className="w-full max-w-2xl bg-white shadow-lg rounded-xl p-6 mb-4 flex-1 flex flex-col">
          <h2 className="text-xl font-semibold mb-4">
            Thai Criminal Law Consultation
          </h2>

          {/* Messages container with scroll */}
          <div
            ref={messagesContainerRef} // Attach the ref here
            className="flex-1 overflow-y-auto mb-4 max-h-[calc(100vh-250px)]"
          >
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
                  } mb-3`}
                >
                  <div
                    className={`px-4 py-2 rounded-lg max-w-[80%] ${
                      msg.sender === "user"
                        ? "bg-blue-500 text-white"
                        : "bg-gray-200"
                    }`}
                  >
                    <div className="text-sm mb-1 font-medium">
                      {msg.sender === "user" ? "You" : "Legal Assistant"}
                    </div>
                    <div
                      className={
                        msg.sender === "user" ? "text-white" : "text-gray-800"
                      }
                    >
                      {formatMessage(msg.message)}
                    </div>
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
            placeholder="Type your response here..."
            className="w-full"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            disabled={isSending}
          />
          <Button
            onClick={handleSendMessage}
            disabled={!message.trim() || isSending}
            className="ml-2"
          >
            {isSending ? "Sending..." : "Send"}
          </Button>
        </div>
      </div>
    </div>
  );
}