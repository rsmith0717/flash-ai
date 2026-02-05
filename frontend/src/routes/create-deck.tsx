import { useMutation } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { AlertCircle, Plus, Save, Trash2 } from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";

export const Route = createFileRoute("/create-deck")({
	component: CreateDeckPage,
});

interface Flashcard {
	question: string;
	answer: string;
}

interface CreateDeckRequest {
	deck_name: string;
	flashcards: Flashcard[];
}

async function createDeck(data: CreateDeckRequest): Promise<void> {
	const token = localStorage.getItem("token");

	if (!token) {
		throw new Error("No authentication token found. Please log in.");
	}

	const response = await fetch("http://localhost:8000/cards/deck/json", {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			Authorization: `Bearer ${token}`,
		},
		body: JSON.stringify(data),
		credentials: "include",
	});

	if (!response.ok) {
		const errorData = await response
			.json()
			.catch(() => ({ detail: "Failed to create deck" }));
		throw new Error(errorData.detail || `Server error: ${response.status}`);
	}
}

function CreateDeckPage() {
	const { user } = useAuth();
	const navigate = useNavigate();
	const [deckName, setDeckName] = useState("");
	const [flashcards, setFlashcards] = useState<Flashcard[]>([
		{ question: "", answer: "" },
	]);

	const createMutation = useMutation({
		mutationFn: createDeck,
		onSuccess: () => {
			// Redirect to practice page after successful creation
			setTimeout(() => {
				navigate({ to: "/practice" });
			}, 1500);
		},
	});

	const addFlashcard = () => {
		setFlashcards([...flashcards, { question: "", answer: "" }]);
	};

	const removeFlashcard = (index: number) => {
		if (flashcards.length > 1) {
			setFlashcards(flashcards.filter((_, i) => i !== index));
		}
	};

	const updateFlashcard = (
		index: number,
		field: "question" | "answer",
		value: string,
	) => {
		const updated = [...flashcards];
		updated[index][field] = value;
		setFlashcards(updated);
	};

	const handleSubmit = (e: React.FormEvent) => {
		e.preventDefault();

		// Validation
		if (!deckName.trim()) {
			return;
		}

		const validFlashcards = flashcards.filter(
			(card) => card.question.trim() && card.answer.trim(),
		);

		if (validFlashcards.length === 0) {
			return;
		}

		createMutation.mutate({
			deck_name: deckName,
			flashcards: validFlashcards,
		});
	};

	const isFormValid =
		deckName.trim() &&
		flashcards.some((card) => card.question.trim() && card.answer.trim());

	// Not logged in
	if (!user) {
		return (
			<div className="container mx-auto px-4 py-8">
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
					<span>Please log in to create a deck</span>
				</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-base-100 py-8">
			<div className="container mx-auto px-4 max-w-4xl">
				{/* Header */}
				<div className="text-center mb-8">
					<div className="avatar placeholder mb-4">
						<div className="bg-gradient-to-br from-primary to-secondary text-primary-content w-16 rounded-full">
							<Plus className="w-8 h-8" />
						</div>
					</div>
					<h1 className="text-3xl font-bold text-base-content mb-2">
						Create New Deck
					</h1>
					<p className="text-base-content/70">
						Manually add flashcards to build your custom study deck
					</p>
				</div>

				{/* Success Message */}
				{createMutation.isSuccess && (
					<div className="alert alert-success mb-6">
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
						<span>Deck created successfully! Redirecting...</span>
					</div>
				)}

				{/* Error Message */}
				{createMutation.error && (
					<div className="alert alert-error mb-6">
						<AlertCircle className="w-5 h-5" />
						<span>{(createMutation.error as Error).message}</span>
					</div>
				)}

				{/* Form */}
				<form onSubmit={handleSubmit} className="space-y-6">
					{/* Deck Name */}
					<div className="card bg-base-200 shadow-xl">
						<div className="card-body p-6">
							<h2 className="card-title text-lg mb-4">Deck Information</h2>
							<div className="form-control w-full">
								<label className="label">
									<span className="label-text font-medium">Deck Name</span>
								</label>
								<input
									type="text"
									placeholder="e.g., Spanish Vocabulary, Biology Chapter 3"
									className="input input-bordered input-primary input-lg w-full"
									value={deckName}
									onChange={(e) => setDeckName(e.target.value)}
									disabled={createMutation.isPending}
									required
								/>
							</div>
						</div>
					</div>

					{/* Flashcards */}
					<div className="space-y-4">
						{flashcards.map((card, index) => (
							<div key={index} className="card bg-base-200 shadow-xl">
								<div className="card-body p-6">
									<div className="flex items-center justify-between mb-6">
										<span className="badge badge-primary badge-lg">
											Card {index + 1}
										</span>
										{flashcards.length > 1 && (
											<button
												type="button"
												onClick={() => removeFlashcard(index)}
												className="btn btn-ghost btn-sm text-error gap-2"
												disabled={createMutation.isPending}
											>
												<Trash2 className="w-4 h-4" />
												Remove
											</button>
										)}
									</div>

									<div className="relative mb-2">
										<textarea
											placeholder=" "
											className="textarea textarea-bordered textarea-primary textarea-md resize-none peer h-30 w-full"
											value={card.question}
											onChange={(e) =>
												updateFlashcard(index, "question", e.target.value)
											}
											disabled={createMutation.isPending}
											required
										/>
										<label className="absolute left-4 top-4 transition-all duration-200 pointer-events-none peer-placeholder-shown:top-4 peer-placeholder-shown:text-base peer-focus:-top-2 peer-focus:text-sm peer-focus:bg-base-200 peer-focus:px-2 peer-focus:text-primary -top-2 text-sm bg-base-200 px-2 text-primary">
											<span className="label-text font-medium">Question</span>
										</label>
									</div>

									<div className="divider my-2"></div>

									<div className="relative mt-2">
										<textarea
											placeholder=" "
											className="textarea textarea-bordered textarea-primary textarea-md resize-none peer h-30 w-full"
											value={card.answer}
											onChange={(e) =>
												updateFlashcard(index, "answer", e.target.value)
											}
											disabled={createMutation.isPending}
											required
										/>
										<label className="absolute left-4 top-4 transition-all duration-200 pointer-events-none peer-placeholder-shown:top-4 peer-placeholder-shown:text-base peer-focus:-top-2 peer-focus:text-sm peer-focus:bg-base-200 peer-focus:px-2 peer-focus:text-primary -top-2 text-sm bg-base-200 px-2 text-primary">
											<span className="label-text font-medium">Answer</span>
										</label>
									</div>
								</div>
							</div>
						))}
					</div>

					{/* Add Card Button */}
					<button
						type="button"
						onClick={addFlashcard}
						className="btn btn-outline btn-primary w-full gap-2"
						disabled={createMutation.isPending}
					>
						<Plus className="w-5 h-5" />
						Add Another Card
					</button>

					{flashcards.length === 0 && (
						<div className="alert alert-info">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
								className="stroke-current shrink-0 w-6 h-6"
							>
								<path
									strokeLinecap="round"
									strokeLinejoin="round"
									strokeWidth="2"
									d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
								/>
							</svg>
							<span>Add at least one flashcard to create a deck</span>
						</div>
					)}

					{/* Submit Buttons */}
					<div className="flex gap-4">
						<button
							type="button"
							onClick={() => navigate({ to: "/" })}
							className="btn btn-ghost flex-1"
							disabled={createMutation.isPending}
						>
							Cancel
						</button>
						<button
							type="submit"
							className="btn btn-primary flex-1 gap-2"
							disabled={!isFormValid || createMutation.isPending}
						>
							{createMutation.isPending ? (
								<>
									<span className="loading loading-spinner loading-sm"></span>
									Creating...
								</>
							) : (
								<>
									<Save className="w-5 h-5" />
									Create Deck
								</>
							)}
						</button>
					</div>
				</form>

				{/* Help Text */}
				<div className="mt-8 text-center">
					<div className="divider"></div>
					<p className="text-base-content/50 text-sm">
						Tip: You can always add more cards to your deck later
					</p>
				</div>
			</div>
		</div>
	);
}
