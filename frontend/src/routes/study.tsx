import { useMutation } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { BookOpen, Bot, RefreshCw, Send, User } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/context/AuthContext";

export const Route = createFileRoute("/study")({
	component: StudyChatPage,
});

interface Message {
	role: "user" | "assistant";
	content: string;
}

interface ChatResponse {
	response: string;
	session_complete: boolean;
	score: number | null;
	total_questions: number;
	questions_answered: number;
}

async function sendChatMessage(message: string): Promise<ChatResponse> {
	const token = localStorage.getItem("token");

	if (!token) {
		throw new Error("No authentication token found. Please log in.");
	}

	const response = await fetch("http://localhost:8000/chat/study", {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			Authorization: `Bearer ${token}`,
		},
		credentials: "include",
		body: JSON.stringify({ message }),
	});

	if (!response.ok) {
		const errorData = await response.json().catch(() => {
			return { detail: "Chat failed" };
		});
		throw new Error(errorData.detail || `Server error: ${response.status}`);
	}

	return response.json();
}

async function resetStudySession(): Promise<void> {
	const token = localStorage.getItem("token");

	if (!token) {
		throw new Error("No authentication token found. Please log in.");
	}

	const response = await fetch("http://localhost:8000/chat/study/reset", {
		method: "POST",
		headers: {
			Authorization: `Bearer ${token}`,
		},
		credentials: "include",
	});

	if (!response.ok) {
		throw new Error("Failed to reset study session");
	}
}

function StudyChatPage() {
	const [messages, setMessages] = useState<Message[]>([]);
	const [input, setInput] = useState("");
	const [sessionStats, setSessionStats] = useState({
		totalQuestions: 0,
		questionsAnswered: 0,
		sessionComplete: false,
	});
	const [hasInitialized, setHasInitialized] = useState(false);
	const messagesEndRef = useRef<HTMLDivElement>(null);
	const { user } = useAuth();

	const scrollToBottom = () => {
		if (messagesEndRef.current) {
			messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
		}
	};

	useEffect(() => {
		scrollToBottom();
	}, [scrollToBottom]);

	const chatMutation = useMutation({
		mutationFn: sendChatMessage,
		onSuccess: (data) => {
			// Add assistant message
			setMessages((prev) => {
				return [
					...prev,
					{
						role: "assistant",
						content: data.response,
					},
				];
			});

			// Update session stats
			setSessionStats({
				totalQuestions: data.total_questions,
				questionsAnswered: data.questions_answered,
				sessionComplete: data.session_complete,
			});
		},
		onError: (error: Error) => {
			setMessages((prev) => {
				return [
					...prev,
					{
						role: "assistant",
						content: `Sorry, I encountered an error: ${error.message}`,
					},
				];
			});
		},
	});

	const resetMutation = useMutation({
		mutationFn: resetStudySession,
		onSuccess: () => {
			// Clear messages and reset stats
			setMessages([]);
			setSessionStats({
				totalQuestions: 0,
				questionsAnswered: 0,
				sessionComplete: false,
			});
			setHasInitialized(false);
			// Trigger greeting again
			setTimeout(() => {
				chatMutation.mutate("");
			}, 100);
		},
		onError: (error: Error) => {
			console.error("Failed to reset session:", error);
		},
	});

	// Initialize session ONCE on mount when user is logged in

	useEffect(() => {
		if (user && !hasInitialized) {
			setHasInitialized(true);
			// Send empty message to trigger greeting
			chatMutation.mutate("");
		}
	}, [
		user,
		hasInitialized, // Send empty message to trigger greeting
		chatMutation.mutate,
	]); // Only depend on user, not on chatMutation

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();
		if (!input.trim() || chatMutation.isPending || !user) return;

		const userMessage = input.trim();

		// Add user message to chat
		setMessages((prev) => {
			return [...prev, { role: "user", content: userMessage }];
		});
		setInput("");

		// Send to backend
		chatMutation.mutate(userMessage);
	};

	const handleReset = () => {
		if (resetMutation.isPending) return;
		resetMutation.mutate();
	};

	return (
		<div className="min-h-screen bg-base-100 flex flex-col">
			{/* Header */}
			<div className="bg-base-200 border-b border-base-300 py-6">
				<div className="container mx-auto px-4">
					<div className="flex items-center justify-between">
						<div className="flex items-center gap-4">
							<div className="avatar placeholder">
								<div className="bg-gradient-to-br from-accent to-secondary text-accent-content w-12 rounded-full">
									<Bot className="w-6 h-6" />
								</div>
							</div>
							<div>
								<h1 className="text-2xl font-bold text-base-content">
									AI Study Assistant
								</h1>
								<p className="text-base-content/70">
									Interactive flashcard study sessions
								</p>
							</div>
						</div>

						{/* Stats and Reset */}
						<div className="flex items-center gap-4">
							{sessionStats.totalQuestions > 0 && (
								<div className="stats shadow bg-base-200">
									<div className="stat py-2 px-4">
										<div className="stat-title text-xs">Progress</div>
										<div className="stat-value text-lg">
											{sessionStats.questionsAnswered}/
											{sessionStats.totalQuestions}
										</div>
									</div>
								</div>
							)}

							<button
								onClick={handleReset}
								className="btn btn-ghost btn-sm gap-2"
								disabled={resetMutation.isPending || chatMutation.isPending}
								title="Start new study session"
							>
								<RefreshCw className="w-4 h-4" />
								<span className="hidden sm:inline">New Session</span>
							</button>
						</div>
					</div>
				</div>
			</div>

			{/* Not Logged In Warning */}
			{!user && (
				<div className="container mx-auto px-4 py-4">
					<div className="alert alert-warning">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							className="stroke-current shrink-0 h-6 w-6"
							fill="none"
							viewBox="0 0 24 24"
						>
							<path
								strokeLinecap="round"
								strokeLinejoin="round"
								strokeWidth="2"
								d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
							/>
						</svg>
						<span>Please log in to start a study session</span>
					</div>
				</div>
			)}

			{/* Messages Area */}
			<div className="flex-1 overflow-y-auto py-8 bg-base-100">
				<div className="container mx-auto px-4 max-w-4xl">
					{messages.length === 0 && !chatMutation.isPending ? (
						<div className="text-center py-16">
							<div className="avatar placeholder mb-4">
								<div className="bg-gradient-to-br from-primary to-secondary text-primary-content w-20 rounded-full">
									<BookOpen className="w-10 h-10" />
								</div>
							</div>
							<h2 className="text-2xl font-bold text-base-content mb-2">
								Start Your Study Session
							</h2>
							<p className="text-base-content/70 mb-4">
								I'll quiz you on flashcards and help you learn!
							</p>
							{user && (
								<p className="text-base-content/50 text-sm">
									Loading study assistant...
								</p>
							)}
						</div>
					) : (
						<div className="space-y-4">
							{messages.map((message, index) => (
								<div
									key={index}
									className={`chat ${message.role === "user" ? "chat-end" : "chat-start"}`}
								>
									<div className="chat-image avatar">
										<div className="w-10 rounded-full">
											{message.role === "user" ? (
												<div className="bg-primary w-full h-full flex items-center justify-center rounded-full">
													<User className="w-5 h-5 text-primary-content" />
												</div>
											) : (
												<div className="bg-gradient-to-br from-accent to-secondary w-full h-full flex items-center justify-center rounded-full">
													<Bot className="w-5 h-5 text-accent-content" />
												</div>
											)}
										</div>
									</div>
									<div
										className={`chat-bubble whitespace-pre-wrap ${
											message.role === "user"
												? "chat-bubble-primary"
												: "chat-bubble-accent"
										}`}
									>
										{message.content}
									</div>
								</div>
							))}

							{chatMutation.isPending && (
								<div className="chat chat-start">
									<div className="chat-image avatar">
										<div className="w-10 rounded-full">
											<div className="bg-gradient-to-br from-accent to-secondary w-full h-full flex items-center justify-center rounded-full">
												<Bot className="w-5 h-5 text-accent-content" />
											</div>
										</div>
									</div>
									<div className="chat-bubble chat-bubble-accent">
										<span className="loading loading-dots loading-sm"></span>
									</div>
								</div>
							)}

							{sessionStats.sessionComplete && (
								<div className="alert alert-success">
									<svg
										xmlns="http://www.w3.org/2000/svg"
										className="stroke-current shrink-0 h-6 w-6"
										fill="none"
										viewBox="0 0 24 24"
									>
										<path
											strokeLinecap="round"
											strokeLinejoin="round"
											strokeWidth="2"
											d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
										/>
									</svg>
									<span>
										Study session complete! Start a new session to study more.
									</span>
								</div>
							)}

							<div ref={messagesEndRef} />
						</div>
					)}
				</div>
			</div>

			{/* Input Area */}
			<div className="bg-base-200 border-t border-base-300 py-4">
				<div className="container mx-auto px-4 max-w-4xl">
					<form onSubmit={handleSubmit} className="flex gap-2">
						<input
							type="text"
							value={input}
							onChange={(e) => setInput(e.target.value)}
							placeholder={
								!user
									? "Please log in to start studying..."
									: sessionStats.sessionComplete
										? "Click 'New Session' to start again..."
										: "Type your answer or topic..."
							}
							className="input input-bordered input-accent flex-1"
							disabled={
								chatMutation.isPending || !user || sessionStats.sessionComplete
							}
						/>
						<button
							type="submit"
							className="btn btn-accent"
							disabled={
								!input.trim() ||
								chatMutation.isPending ||
								!user ||
								sessionStats.sessionComplete
							}
						>
							{chatMutation.isPending ? (
								<span className="loading loading-spinner loading-sm"></span>
							) : (
								<Send className="w-5 h-5" />
							)}
						</button>
					</form>

					{/* Helper Text */}
					{user && messages.length > 0 && !sessionStats.sessionComplete && (
						<p className="text-xs text-base-content/50 mt-2 text-center">
							{sessionStats.totalQuestions > 0
								? "Answer the question and type 'next' to continue"
								: "Tell me what topic you'd like to study"}
						</p>
					)}
				</div>
			</div>
		</div>
	);
}
