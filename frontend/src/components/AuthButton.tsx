import { Link } from "@tanstack/react-router";
import { LogIn, LogOut, User } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export function AuthButton() {
	const { user, logout } = useAuth();

	if (user) {
		return (
			<div className="flex items-center gap-4">
				<span className="text-gray-300 flex items-center gap-2">
					<User size={16} />
					{user.email}
				</span>
				<button
					onClick={logout}
					className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-white transition-colors"
				>
					<LogOut size={16} />
					Logout
				</button>
			</div>
		);
	}

	return (
		<Link
			to="/login"
			className="flex items-center gap-2 px-4 py-2 bg-cyan-500 hover:bg-cyan-600 rounded-lg text-white transition-colors"
		>
			<LogIn size={16} />
			Login
		</Link>
	);
}
