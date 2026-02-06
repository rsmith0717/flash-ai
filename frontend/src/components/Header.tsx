import { Link } from "@tanstack/react-router";
import {
	Home,
	LogIn,
	LogOut,
	Menu,
	User,
	X,
} from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";

export default function Header() {
	const [isOpen, setIsOpen] = useState(false);
	const [groupedExpanded, setGroupedExpanded] = useState<
		Record<string, boolean>
	>({});
	const { user, logout } = useAuth();

	return (
		<>
			<header className="p-4 flex items-center justify-between bg-gray-800 text-white shadow-lg">
				<div className="flex items-center">
					<button
						onClick={() => setIsOpen(true)}
						className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
						aria-label="Open menu"
					>
						<Menu size={24} />
					</button>
					<h1 className="ml-4 text-xl font-semibold">
						<Link to="/">
							<span className="font-bold">Flash AI</span>
						</Link>
					</h1>
				</div>

				{/* Auth Button */}
				<div className="flex items-center">
					{user ? (
						<div className="flex items-center gap-3">
							<span className="hidden sm:flex items-center gap-2 text-gray-300 text-sm">
								<User size={16} />
								{user.email}
							</span>
							<button
								onClick={logout}
								className="flex items-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-white text-sm transition-colors"
							>
								<LogOut size={16} />
								<span className="hidden sm:inline">Logout</span>
							</button>
						</div>
					) : (
						<Link
							to="/login"
							className="flex items-center gap-2 px-4 py-2 bg-cyan-500 hover:bg-cyan-600 rounded-lg text-white text-sm font-medium transition-colors shadow-lg shadow-cyan-500/25"
						>
							<LogIn size={16} />
							<span className="hidden sm:inline">Login</span>
						</Link>
					)}
				</div>
			</header>

			<aside
				className={`fixed top-0 left-0 h-full w-80 bg-gray-900 text-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out flex flex-col ${
					isOpen ? "translate-x-0" : "-translate-x-full"
				}`}
			>
				<div className="flex items-center justify-between p-4 border-b border-gray-700">
					<h2 className="text-xl font-bold">Navigation</h2>
					<button
						onClick={() => setIsOpen(false)}
						className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
						aria-label="Close menu"
					>
						<X size={24} />
					</button>
				</div>

				{/* User Info in Sidebar (when logged in) */}
				{user && (
					<div className="p-4 border-b border-gray-700 bg-gray-800/50">
						<div className="flex items-center gap-3">
							<div className="w-10 h-10 bg-cyan-500 rounded-full flex items-center justify-center">
								<User size={20} />
							</div>
							<div className="flex-1 min-w-0">
								<p className="text-sm font-medium text-white truncate">
									{user.email}
								</p>
								<p className="text-xs text-gray-400">Logged in</p>
							</div>
						</div>
					</div>
				)}

				<nav className="flex-1 p-4 overflow-y-auto">
					<Link
						to="/"
						onClick={() => setIsOpen(false)}
						className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-800 transition-colors mb-2"
						activeProps={{
							className:
								"flex items-center gap-3 p-3 rounded-lg bg-cyan-600 hover:bg-cyan-700 transition-colors mb-2",
						}}
					>
						<Home size={20} />
						<span className="font-medium">Home</span>
					</Link>

					
				</nav>

				{/* Sidebar Footer with Login/Logout */}
				<div className="p-4 border-t border-gray-700">
					{user ? (
						<button
							onClick={() => {
								logout();
								setIsOpen(false);
							}}
							className="w-full flex items-center justify-center gap-2 p-3 bg-slate-700 hover:bg-slate-600 rounded-lg text-white transition-colors"
						>
							<LogOut size={20} />
							<span className="font-medium">Logout</span>
						</button>
					) : (
						<Link
							to="/login"
							onClick={() => setIsOpen(false)}
							className="w-full flex items-center justify-center gap-2 p-3 bg-cyan-500 hover:bg-cyan-600 rounded-lg text-white transition-colors"
						>
							<LogIn size={20} />
							<span className="font-medium">Login</span>
						</Link>
					)}
				</div>
			</aside>

			{/* Overlay when sidebar is open */}
			{isOpen && (
				<div
					className="fixed inset-0 bg-black/50 z-40"
					onClick={() => setIsOpen(false)}
				/>
			)}
		</>
	);
}
