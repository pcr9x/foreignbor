"use client"

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

export default function Home() {
  const [message, setMessage] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const router = useRouter();

  // Function to handle submitting the message
  const handleSendMessage = async () => {
    if (!message.trim()) return;

    try {
      // Create a new chat and get the conversationId (this could be an API call)
      const response = await fetch("http://localhost:8000/generate-answer", {
        method: "POST",
        body: JSON.stringify({ message }),
        headers: {
          "Content-Type": "application/json",
        },
      });
      const data = await response.json();
      const newConversationId = data.conversationId;

      // Set the conversationId
      setConversationId(newConversationId);

      // Redirect to the chat page
      router.push(`/chat/${newConversationId}`);
    } catch (error) {
      console.error("Error starting chat:", error);
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center p-4 bg-gray-100">
      <div className="w-full max-w-2xl bg-white shadow-lg rounded-xl p-6">
        <h1 className="text-2xl font-semibold text-center mb-4">
          Ask me about foreign labor laws in Thailand!
        </h1>
        <div className="grid gap-4">
          <Textarea
            placeholder="Type your message here."
            className="w-full"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
          />
          <Button
            className="w-full"
            disabled={!message.trim()}
            onClick={handleSendMessage}
          >
            Send message
          </Button>
        </div>
      </div>
    </div>
  );
}