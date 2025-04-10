"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

export default function Home() {
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const [userId, setUserId] = useState<string | null>(null);
  
  // Get the user_id from localStorage
  useEffect(() => {
    const storedUserId = localStorage.getItem("user_id");
    if (storedUserId) {
      setUserId(storedUserId);
    }
  }, []);

  // Function to handle submitting the message
  const handleSendMessage = async () => {
    if (!message.trim()) return;

    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/generate-answer", {
        method: "POST",
        body: JSON.stringify({ message, user_id: userId }),
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to send message");
      }

      const data = await response.json();
      const newConversationId = data.conversationId;

      // Redirect to the chat page
      router.push(`/chat/${newConversationId}`);
    } catch (error) {
      console.error("Error starting chat:", error);
      alert("There was an error processing your request. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center p-4 bg-gray-100">
      <div className="w-full max-w-2xl bg-white shadow-lg rounded-xl p-6">
        <h1 className="text-2xl font-semibold text-center mb-4">
          Ask me about Penal Code / Criminal Law in Thailand!
        </h1>
        <p className="text-gray-600 mb-6 text-center">
          Describe your legal situation in detail. I&apos;ll help analyze your
          case based on Thai criminal law.
        </p>
        <div className="grid gap-4">
          <Textarea
            placeholder="Example: A person attacked someone with a knife, causing serious injury. The victim was a police officer on duty."
            className="w-full min-h-[120px]"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
          />
          <Button
            className="w-full"
            disabled={!message.trim() || isLoading}
            onClick={handleSendMessage}
          >
            {isLoading ? "Processing..." : "Send message"}
          </Button>
        </div>
      </div>
    </div>
  );
}