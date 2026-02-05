import { createFileRoute } from "@tanstack/react-router";
import {
	BookOpen,
	FileJson,
	FileText,
	MessageSquare,
	Plus,
	Search,
	Sparkles,
} from "lucide-react";
import FeatureCard from "@/components/FeatureCard";

export const Route = createFileRoute("/")({ component: App });

function App() {
	const colorSchemes = {
		pink: {
			gradient: "bg-gradient-to-br from-pink-500 to-purple-500",
			iconBg: "bg-primary/20",
			iconText: "text-primary",
			border: "hover:border-primary",
			shadow: "hover:shadow-primary/20",
			btnClass: "btn-primary",
		},
		purple: {
			gradient: "bg-gradient-to-br from-purple-500 to-pink-500",
			iconBg: "bg-secondary/20",
			iconText: "text-secondary",
			border: "hover:border-secondary",
			shadow: "hover:shadow-secondary/20",
			btnClass: "btn-secondary",
		},
		cyan: {
			gradient: "bg-gradient-to-br from-cyan-500 to-blue-500",
			iconBg: "bg-accent/20",
			iconText: "text-accent",
			border: "hover:border-accent",
			shadow: "hover:shadow-accent/20",
			btnClass: "btn-accent",
		},
		green: {
			gradient: "bg-gradient-to-br from-green-500 to-emerald-500",
			iconBg: "bg-success/20",
			iconText: "text-success",
			border: "hover:border-success",
			shadow: "hover:shadow-success/20",
			btnClass: "btn-success",
		},
		orange: {
			gradient: "bg-gradient-to-br from-orange-500 to-red-500",
			iconBg: "bg-warning/20",
			iconText: "text-warning",
			border: "hover:border-warning",
			shadow: "hover:shadow-warning/20",
			btnClass: "btn-warning",
		},
		blue: {
			gradient: "bg-gradient-to-br from-blue-500 to-indigo-500",
			iconBg: "bg-info/20",
			iconText: "text-info",
			border: "hover:border-info",
			shadow: "hover:shadow-info/20",
			btnClass: "btn-info",
		},
	};

	return (
		<div className="min-h-screen bg-base-100">
			<div className="container mx-auto px-4 py-16">
				{/* Header */}
				<div className="text-center mb-16">
					<div className="avatar placeholder mb-6">
						<div className="bg-gradient-to-br from-primary to-secondary text-primary-content w-20 rounded-full">
							<Sparkles className="w-10 h-10" />
						</div>
					</div>
					<h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
						Flash AI
					</h1>
					<p className="text-xl text-base-content/70 max-w-2xl mx-auto">
						AI-powered flashcard learning platform with intelligent study
						features
					</p>
				</div>

				{/* Feature Cards Grid */}
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
					<FeatureCard
						to="/create-deck"
						icon={Plus}
						title="Create Deck"
						description="Manually create a new flashcard deck by adding questions and answers one by one"
						colorScheme={colorSchemes.pink}
					/>

					<FeatureCard
						to="/upload-json"
						icon={FileJson}
						title="Upload JSON Deck"
						description="Create a new flashcard deck by uploading a JSON file with questions and answers"
						colorScheme={colorSchemes.purple}
					/>

					<FeatureCard
						to="/upload-text"
						icon={FileText}
						title="Upload Text Document"
						description="Create flashcards from a .txt document and let AI process the content"
						colorScheme={colorSchemes.cyan}
					/>

					<FeatureCard
						to="/practice"
						icon={BookOpen}
						title="Practice Flashcards"
						description="Study your flashcard decks with a traditional flip-card interface"
						colorScheme={colorSchemes.orange}
					/>

					<FeatureCard
						to="/search"
						icon={Search}
						title="Search Flashcards"
						description="Find relevant flashcards by topic using AI-powered semantic search"
						colorScheme={colorSchemes.green}
					/>

					<FeatureCard
						to="/study"
						icon={MessageSquare}
						title="AI Study Assistant"
						description="Chat with an AI tutor that helps you study using your flashcard content"
						colorScheme={colorSchemes.blue}
					/>
				</div>

				{/* Footer */}
				<div className="mt-16 text-center">
					<div className="divider"></div>
					<p className="text-base-content/50 text-sm">
						All features are powered by AI embeddings and semantic search
					</p>
				</div>
			</div>
		</div>
	);
}
