"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/app/context/AuthContext";

export function ProfileMenu() {
  const { isAuthenticated, setIsAuthenticated } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    setIsAuthenticated(false); // Update the global authentication state
    router.push("/flow/login"); // Redirect to login
    router.refresh();
  };

  return (
    <div className="relative">
      <div className="fixed top-4 right-4">
        {isAuthenticated ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="w-10 h-10 rounded-full bg-blue-500 hover:bg-blue-600 transition" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => router.push("/profile")}>
                Manage Profile
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleLogout}>Logout</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ) : (
          <Button onClick={() => router.push("/flow/login")}>Sign In</Button>
        )}
      </div>
    </div>
  );
}
