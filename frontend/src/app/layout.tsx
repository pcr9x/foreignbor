"use client";

import { Geist, Geist_Mono } from "next/font/google";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { Pencil } from "lucide-react";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { ProfileMenu } from "../components/ProfileMenu";
import "./globals.css";
import { AppSidebar } from "../components/app-sidebar";
import { AuthProvider } from "../app/context/AuthContext";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [open, setOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    setIsAuthenticated(!!token);
  }, []);

  const redirectToHome = () => {
    router.push("/");
  };

  return (
    <html lang="en">
      <head>
        <title>Foreignbor</title>
        <meta
          name="description"
          content="AI-powered assistant for foreign worker laws in Thailand."
        />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <AuthProvider>
          <SidebarProvider open={open} onOpenChange={setOpen}>
            <div className="flex flex-col min-h-screen w-full">
              <ProfileMenu />
              <div className="flex flex-1 w-full">
                {isAuthenticated && (
                  <>
                    <AppSidebar />
                    {/* Hide SidebarTrigger and Pencil when sidebar is open */}
                    {!open && (
                      <div className="flex pt-3 pl-4">
                        <SidebarTrigger />
                        <Button
                          variant="ghost"
                          size="icon"
                          className={cn("h-7 w-7", "ml-2")}
                          onClick={redirectToHome}
                        >
                          <Pencil />
                        </Button>
                      </div>
                    )}
                  </>
                )}
                <main className="flex-1 flex flex-col">{children}</main>
              </div>
            </div>
          </SidebarProvider>
        </AuthProvider>
      </body>
    </html>
  );
}