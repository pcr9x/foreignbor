"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupAction,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuAction,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import { MoreHorizontal, Trash2, Pencil } from "lucide-react";

interface Chat {
  id: string;
  title: string;
  last_updated: string;
}

export function AppSidebar() {
  const [chats, setChats] = useState<Chat[]>([]);
  const router = useRouter();

  useEffect(() => {
    async function fetchChats() {
      try {
        const res = await fetch("http://localhost:8000/chats");
        if (!res.ok) throw new Error("Failed to fetch chats");
        const data = await res.json();
        setChats(data.chats || []);
      } catch (error) {
        console.error("Error fetching chats:", error);
      }
    }
    fetchChats();
  }, []);

  // Navigate to chat page
  const handleSelectChat = (chatId: string) => {
    router.push(`/chat/${chatId}`);
  };

  // Delete chat with confirmation
  const handleDeleteChat = async (chatId: string) => {
    const isConfirmed = window.confirm(
      "Are you sure you want to delete this chat? This action cannot be undone."
    );

    if (isConfirmed) {
      try {
        await fetch(`http://localhost:8000/chat/${chatId}`, {
          method: "DELETE",
        });
        setChats((prevChats) => prevChats.filter((chat) => chat.id !== chatId));
        router.push("/"); // Redirect to home page or wherever after deletion
      } catch (error) {
        console.error("Error deleting chat:", error);
      }
    }
  };

  // Group chats by date
  const groupedChats = {
    today: [] as Chat[],
    last7Days: [] as Chat[],
    last30Days: [] as Chat[],
    older: [] as Chat[],
  };

  const now = new Date();
  chats.forEach((chat) => {
    const chatDate = new Date(chat.last_updated);
    const diffDays = Math.floor(
      (now.getTime() - chatDate.getTime()) / (1000 * 60 * 60 * 24)
    );

    if (diffDays <= 0) groupedChats.today.push(chat);
    else if (diffDays <= 7) groupedChats.last7Days.push(chat);
    else if (diffDays <= 30) groupedChats.last30Days.push(chat);
    else groupedChats.older.push(chat);
  });

  return (
    <Sidebar>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>
            <SidebarTrigger />
          </SidebarGroupLabel>
          <SidebarGroupAction title="New Chat" onClick={() => router.push("/")}>
            <Pencil /> <span className="sr-only">New Chat</span>
          </SidebarGroupAction>
          <SidebarGroupContent>
            <SidebarMenu>
              {Object.entries(groupedChats).map(([label, chats]) =>
                chats.length > 0 ? (
                  <SidebarMenuSub key={label}>
                    <SidebarMenuItem>
                      <span className="font-semibold">
                        {label === "today"
                          ? "Today"
                          : label === "last7Days"
                          ? "Previous 7 Days"
                          : label === "last30Days"
                          ? "Previous 30 Days"
                          : "Older"}
                      </span>
                    </SidebarMenuItem>

                    {chats.map((chat) => (
                      <SidebarMenuItem key={chat.id}>
                        <SidebarMenuButton asChild>
                          <a
                            href="#"
                            onClick={(e) => {
                              e.preventDefault();
                              handleSelectChat(chat.id);
                            }}
                          >
                            <span>{chat.title}</span>
                          </a>
                        </SidebarMenuButton>

                        {/* Dropdown Menu for Delete */}
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <SidebarMenuAction>
                              <MoreHorizontal />
                            </SidebarMenuAction>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent side="right" align="start">
                            <DropdownMenuItem
                              className="text-red-500"
                              onClick={() => handleDeleteChat(chat.id)}
                            >
                              <Trash2 className="mr-2" size={16} />
                              <span>Delete</span>
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </SidebarMenuItem>
                    ))}
                  </SidebarMenuSub>
                ) : null
              )}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
