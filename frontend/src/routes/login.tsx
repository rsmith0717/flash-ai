import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { AlertCircle, Lock, LogIn, Mail } from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";

export const Route = createFileRoute("/login")({
	component: LoginPage,
});

function LoginPage() {
	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");
	const { login, isLoading, error } = useAuth();
	const navigate = useNavigate();

	const handleSubmit = async (e: React.SyntheticEvent<HTMLFormElement>) => {
		e.preventDefault();

		try {
			await login(email, password);
			navigate({ to: "/" });
		} catch (_err) {
			// Error is handled by the auth context
		}
	};

	return (
		<div className="flex items-center justify-center min-h-screen bg-base-100 p-4">
			<div className="w-full max-w-md">
				<div className="card bg-base-200 shadow-xl border border-base-300">
					<div className="card-body items-center">
						{/* Header */}
						<div className="text-center mb-6">
							<div className="avatar placeholder mb-4">
								<div className="bg-gradient-to-br from-primary to-accent text-primary-content w-16 rounded-full">
									<LogIn className="w-8 h-8" />
								</div>
							</div>
							<h1 className="text-2xl font-bold text-base-content">Welcome Back</h1>
							<p className="text-base-content/70 mt-2">Sign in to your account</p>
						</div>

						{/* Error Message */}
						{error && (
							<div className="alert alert-error mb-6 w-full">
								<AlertCircle className="w-5 h-5" />
								<span className="text-sm">{error}</span>
							</div>
						)}

						{/* Login Form */}
						<form onSubmit={handleSubmit} className="space-y-4 w-full">
							<div className="form-control w-full">
								<label htmlFor="email" className="label">
									<span className="label-text">Email Address</span>
								</label>
								<label className="input input-bordered flex items-center gap-2 w-full">
									<Mail className="w-4 h-4 opacity-70" />
									<input
										id="email"
										type="email"
										value={email}
										onChange={(e) => setEmail(e.target.value)}
										placeholder="you@example.com"
										required
										className="grow"
									/>
								</label>
							</div>

							<div className="form-control w-full">
								<label htmlFor="password" className="label">
									<span className="label-text">Password</span>
								</label>
								<label className="input input-bordered flex items-center gap-2 w-full">
									<Lock className="w-4 h-4 opacity-70" />
									<input
										id="password"
										type="password"
										value={password}
										onChange={(e) => setPassword(e.target.value)}
										placeholder="••••••••"
										required
										className="grow"
									/>
								</label>
							</div>

							<button
								type="submit"
								disabled={isLoading}
								className="btn btn-primary w-full"
							>
								{isLoading ? (
									<>
										<span className="loading loading-spinner loading-sm"></span>
										Signing in...
									</>
								) : (
									"Sign In"
								)}
							</button>
						</form>

						{/* Test Credentials Hint */}
						<div className="alert alert-info mt-6 w-full">
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
							<div className="text-sm">
								<span className="font-medium">Test credentials:</span>
								<br />
								<span className="font-mono">tester@test.com / testpass</span>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	);
}