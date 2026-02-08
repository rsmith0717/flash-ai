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
	const { user, logout } = useAuth();

	return (
		<>
			<header className="navbar bg-base-200 shadow-lg border-b border-base-300">
				<div className="navbar-start">
					<button
						onClick={() => setIsOpen(true)}
						className="btn btn-ghost btn-circle"
						aria-label="Open menu"
					>
						<Menu size={24} />
					</button>
					<Link to="/" className="btn btn-ghost text-xl font-bold normal-case">
						<span className="bg-linear-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
							Flash AI
						</span>
					</Link>
				</div>

				{/* Auth Section */}
				<div className="navbar-end">
					{user ? (
						<div className="flex items-center gap-3">
							<span className="hidden sm:flex items-center gap-2 text-base-content/70 text-sm">
								<User size={16} />
								{user.email}
							</span>
							<button
								onClick={logout}
								className="btn btn-ghost btn-sm gap-2"
							>
								<LogOut size={16} />
								<span className="hidden sm:inline">Logout</span>
							</button>
						</div>
					) : (
						<Link
							to="/login"
							className="btn btn-primary btn-sm gap-2"
						>
							<LogIn size={16} />
							<span className="hidden sm:inline">Login</span>
						</Link>
					)}
				</div>
			</header>

			{/* Sidebar Drawer */}
			<aside
				className={`fixed top-0 left-0 h-full w-80 bg-base-200 border-r border-base-300 shadow-2xl z-50 transform transition-transform duration-300 ease-in-out flex flex-col ${
					isOpen ? "translate-x-0" : "-translate-x-full"
				}`}
			>
				{/* Sidebar Header */}
				<div className="flex items-center justify-between p-4 border-b border-base-300">
					<h2 className="text-xl font-bold text-base-content">Navigation</h2>
					<button
						onClick={() => setIsOpen(false)}
						className="btn btn-ghost btn-sm btn-circle"
						aria-label="Close menu"
					>
						<X size={24} />
					</button>
				</div>

				{/* User Info in Sidebar (when logged in) */}
				{user && (
					<div className="p-4 border-b border-base-300 bg-base-300/50">
						<div className="flex items-center gap-3">
							<div className="avatar placeholder">
								<div className="bg-accent text-accent-content w-10 rounded-full">
									<User size={20} />
								</div>
							</div>
							<div className="flex-1 min-w-0">
								<p className="text-sm font-medium text-base-content truncate">
									{user.email}
								</p>
								<p className="text-xs text-base-content/50">Logged in</p>
							</div>
						</div>
					</div>
				)}

				{/* Navigation Links */}
				<nav className="flex-1 p-4 overflow-y-auto">
					<ul className="menu menu-lg">
						<li>
							<Link
								to="/"
								onClick={() => setIsOpen(false)}
								className="gap-3"
								activeProps={{
									className: "active bg-primary text-primary-content gap-3",
								}}
							>
								<Home size={20} />
								<span className="font-medium">Home</span>
							</Link>
						</li>
					</ul>
				</nav>

				{/* Sidebar Footer with Login/Logout */}
				<div className="p-4 border-t border-base-300">
					{user ? (
						<button
							onClick={() => {
								logout();
								setIsOpen(false);
							}}
							className="btn btn-ghost w-full gap-2"
						>
							<LogOut size={20} />
							<span className="font-medium">Logout</span>
						</button>
					) : (
						<Link
							to="/login"
							onClick={() => setIsOpen(false)}
							className="btn btn-primary w-full gap-2"
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