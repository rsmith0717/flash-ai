import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { BookOpen, ChevronRight, RotateCcw, Shuffle } from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";

export const Route = createFileRoute("/practice")({
	component: PracticePage,
});

interface Deck {
	id: number;
	name: string;
	user_id: string;
}

interface Flashcard {
	question: string;
	answer: string;
}

async function fetchUserDecks(): Promise<Deck[]> {
	const token = localStorage.getItem("token");

	if (!token) {
		throw new Error("No authentication token found. Please log in.");
	}

	const response = await fetch("http://localhost:8000/cards/decks", {
		headers: {
			Authorization: `Bearer ${token}`,
		},
		credentials: "include",
	});

	if (!response.ok) {
		const errorData = await response
			.json()
			.catch(() => ({ detail: "Failed to fetch decks" }));
		throw new Error(errorData.detail || `Server error: ${response.status}`);
	}

	return response.json();
}

async function fetchDeckCards(deckId: number): Promise<Flashcard[]> {
	const token = localStorage.getItem("token");

	if (!token) {
		throw new Error("No authentication token found. Please log in.");
	}

	const response = await fetch(
		`http://localhost:8000/cards/deck/${deckId}/cards`,
		{
			headers: {
				Authorization: `Bearer ${token}`,
			},
			credentials: "include",
		},
	);

	if (!response.ok) {
		const errorData = await response
			.json()
			.catch(() => ({ detail: "Failed to fetch cards" }));
		throw new Error(errorData.detail || `Server error: ${response.status}`);
	}

	return response.json();
}

function PracticePage() {
	const { user } = useAuth();
	const [selectedDeckId, setSelectedDeckId] = useState<number | null>(null);
	const [currentCardIndex, setCurrentCardIndex] = useState(0);
	const [isFlipped, setIsFlipped] = useState(false);
	const [shuffledCards, setShuffledCards] = useState<Flashcard[]>([]);

	const decksQuery = useQuery({
		queryKey: ["decks"],
		queryFn: fetchUserDecks,
		enabled: !!user,
	});

	const cardsQuery = useQuery({
		queryKey: ["deck-cards", selectedDeckId],
		queryFn: () => fetchDeckCards(selectedDeckId!),
		enabled: !!selectedDeckId,
	});

	const handleDeckSelect = (deckId: number) => {
		setSelectedDeckId(deckId);
		setCurrentCardIndex(0);
		setIsFlipped(false);
	};

	const handleShuffle = () => {
		if (cardsQuery.data) {
			const shuffled = [...cardsQuery.data].sort(() => Math.random() - 0.5);
			setShuffledCards(shuffled);
			setCurrentCardIndex(0);
			setIsFlipped(false);
		}
	};

	const handleReset = () => {
		setShuffledCards([]);
		setCurrentCardIndex(0);
		setIsFlipped(false);
	};

	const handleFlip = () => {
		setIsFlipped(true);
	};

	const handleNext = () => {
		const cards =
			shuffledCards.length > 0 ? shuffledCards : cardsQuery.data || [];
		if (currentCardIndex < cards.length - 1) {
			setCurrentCardIndex(currentCardIndex + 1);
			setIsFlipped(false);
		}
	};

	const cards =
		shuffledCards.length > 0 ? shuffledCards : cardsQuery.data || [];
	const currentCard = cards[currentCardIndex];
	const progress =
		cards.length > 0 ? ((currentCardIndex + 1) / cards.length) * 100 : 0;

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
					<span>Please log in to practice flashcards</span>
				</div>
			</div>
		);
	}

	// Deck selection screen
	if (!selectedDeckId) {
		return (
			<div className="min-h-screen bg-base-100 py-8">
				<div className="container mx-auto px-4 max-w-4xl">
					{/* Header */}
					<div className="text-center mb-8">
						<div className="avatar placeholder mb-4">
							<div className="bg-gradient-to-br from-accent to-secondary text-accent-content w-16 rounded-full">
								<BookOpen className="w-8 h-8" />
							</div>
						</div>
						<h1 className="text-3xl font-bold text-base-content mb-2">
							Practice Flashcards
						</h1>
						<p className="text-base-content/70">
							Select a deck to start practicing
						</p>
					</div>

					{/* Deck List */}
					{decksQuery.isLoading && (
						<div className="flex justify-center py-12">
							<span className="loading loading-spinner loading-lg"></span>
						</div>
					)}

					{decksQuery.error && (
						<div className="alert alert-error">
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
									d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
								/>
							</svg>
							<span>{(decksQuery.error as Error).message}</span>
						</div>
					)}

					{decksQuery.data && decksQuery.data.length === 0 && (
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
							<span>
								You don't have any decks yet. Create one to start practicing!
							</span>
						</div>
					)}

					{decksQuery.data && decksQuery.data.length > 0 && (
						<div className="grid gap-4 md:grid-cols-2">
							{decksQuery.data.map((deck) => (
								<button
									key={deck.id}
									onClick={() => handleDeckSelect(deck.id)}
									className="card bg-base-200 hover:bg-base-300 transition-colors text-left"
								>
									<div className="card-body">
										<h2 className="card-title text-base-content">
											{deck.name}
										</h2>
										<div className="card-actions justify-end">
											<ChevronRight className="w-5 h-5 text-primary" />
										</div>
									</div>
								</button>
							))}
						</div>
					)}
				</div>
			</div>
		);
	}

	// Flashcard practice screen
	return (
		<div className="min-h-screen bg-base-100 py-8">
			<div className="container mx-auto px-4 max-w-2xl">
				{/* Header with controls */}
				<div className="flex items-center justify-between mb-6">
					<button
						onClick={() => setSelectedDeckId(null)}
						className="btn btn-ghost btn-sm"
					>
						← Back to Decks
					</button>
					<div className="flex gap-2">
						<button
							onClick={handleShuffle}
							className="btn btn-outline btn-sm gap-2"
							disabled={!cardsQuery.data || cardsQuery.data.length === 0}
						>
							<Shuffle className="w-4 h-4" />
							Shuffle
						</button>
						<button
							onClick={handleReset}
							className="btn btn-outline btn-sm gap-2"
							disabled={shuffledCards.length === 0}
						>
							<RotateCcw className="w-4 h-4" />
							Reset
						</button>
					</div>
				</div>

				{/* Loading state */}
				{cardsQuery.isLoading && (
					<div className="flex justify-center py-12">
						<span className="loading loading-spinner loading-lg"></span>
					</div>
				)}

				{/* Error state */}
				{cardsQuery.error && (
					<div className="alert alert-error">
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
								d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
							/>
						</svg>
						<span>{(cardsQuery.error as Error).message}</span>
					</div>
				)}

				{/* Empty state */}
				{cardsQuery.data && cardsQuery.data.length === 0 && (
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
						<span>This deck doesn't have any flashcards yet.</span>
					</div>
				)}

				{/* Flashcard */}
				{currentCard && (
					<div className="space-y-6">
						{/* Progress bar */}
						<div>
							<div className="flex justify-between text-sm text-base-content/70 mb-2">
								<span>
									Card {currentCardIndex + 1} of {cards.length}
								</span>
								<span>{Math.round(progress)}% Complete</span>
							</div>
							<progress
								className="progress progress-primary w-full"
								value={progress}
								max="100"
							></progress>
						</div>

						{/* Card */}
						<div
							className="card bg-base-200 shadow-xl border-2 border-primary/20 min-h-[400px] cursor-pointer"
							onClick={!isFlipped ? handleFlip : undefined}
						>
							<div className="card-body items-center justify-center text-center p-8">
								<div className="badge badge-primary mb-4">
									{isFlipped ? "Answer" : "Question"}
								</div>
								<div className="text-2xl font-medium text-base-content">
									{isFlipped ? currentCard.answer : currentCard.question}
								</div>
								{!isFlipped && (
									<p className="text-sm text-base-content/50 mt-4">
										Click to reveal answer
									</p>
								)}
							</div>
						</div>

						{/* Action buttons */}
						<div className="flex gap-4">
							{!isFlipped ? (
								<button
									onClick={handleFlip}
									className="btn btn-primary btn-block btn-lg"
								>
									Show Answer
								</button>
							) : currentCardIndex < cards.length - 1 ? (
								<button
									onClick={handleNext}
									className="btn btn-primary btn-block btn-lg gap-2"
								>
									Next Card
									<ChevronRight className="w-5 h-5" />
								</button>
							) : (
								<button
									onClick={() => {
										setCurrentCardIndex(0);
										setIsFlipped(false);
									}}
									className="btn btn-success btn-block btn-lg gap-2"
								>
									<RotateCcw className="w-5 h-5" />
									Practice Again
								</button>
							)}
						</div>
					</div>
				)}
			</div>
		</div>
	);
}
