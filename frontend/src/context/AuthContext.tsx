import {
	createContext,
	type ReactNode,
	useCallback,
	useContext,
	useEffect,
	useRef,
	useState,
} from "react";

interface User {
	id: string;
	email: string;
}

interface AuthContextType {
	user: User | null;
	token: string | null;
	login: (email: string, password: string) => Promise<void>;
	logout: () => void;
	isLoading: boolean;
	error: string | null;
}

const AuthContext = createContext<AuthContextType | null>(null);

const BACKEND_URL = "http://localhost:8000";

export function AuthProvider({ children }: { children: ReactNode }) {
	const [user, setUser] = useState<User | null>(null);
	const [token, setToken] = useState<string | null>(() => {
		if (typeof window !== "undefined") {
			return localStorage.getItem("token");
		}
		return null;
	});
	const [isLoading, setIsLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	// Track if we've already fetched user data
	const hasFetchedUser = useRef(false);

	// Fetch user data when token exists - only once
	useEffect(() => {
		// Skip if no token, already fetched, or user already set
		if (!token || hasFetchedUser.current || user) {
			return;
		}

		const fetchUser = async () => {
			hasFetchedUser.current = true;

			try {
				const response = await fetch(
					`${BACKEND_URL}/auth/authenticated-route`,
					{
						headers: {
							Authorization: `Bearer ${token}`,
						},
					},
				);

				if (response.ok) {
					const data = await response.json();
					// Extract email from the response message
					const emailMatch = data.message?.match(/Hello (.+)!/);
					if (emailMatch) {
						setUser({ id: "", email: emailMatch[1] });
					}
				} else {
					// Token is invalid, clear it
					localStorage.removeItem("token");
					setToken(null);
					setUser(null);
				}
			} catch (err) {
				console.error("Failed to fetch user:", err);
			}
		};

		fetchUser();
	}, [token, user]);

	// Reset the fetch flag when token changes (e.g., after logout and new login)
	useEffect(() => {
		if (!token) {
			hasFetchedUser.current = false;
		}
	}, [token]);

	const login = useCallback(async (email: string, password: string) => {
		setIsLoading(true);
		setError(null);

		try {
			// fastapi-users expects form data for login
			const formData = new URLSearchParams();
			formData.append("username", email); // fastapi-users uses 'username' field for email
			formData.append("password", password);

			const response = await fetch(`${BACKEND_URL}/auth/jwt/login`, {
				method: "POST",
				headers: {
					"Content-Type": "application/x-www-form-urlencoded",
				},
				body: formData,
			});

			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.detail || "Login failed");
			}

			const data = await response.json();
			const accessToken = data.access_token;

			// Store token and set user directly (no need to fetch again)
			localStorage.setItem("token", accessToken);
			hasFetchedUser.current = true; // Mark as fetched since we know the user
			setToken(accessToken);
			setUser({ id: "", email });
		} catch (err) {
			setError(err instanceof Error ? err.message : "Login failed");
			throw err;
		} finally {
			setIsLoading(false);
		}
	}, []);

	const logout = useCallback(() => {
		localStorage.removeItem("token");
		setToken(null);
		setUser(null);
		hasFetchedUser.current = false;
	}, []);

	return (
		<AuthContext.Provider
			value={{ user, token, login, logout, isLoading, error }}
		>
			{children}
		</AuthContext.Provider>
	);
}

export function useAuth() {
	const context = useContext(AuthContext);
	if (!context) {
		throw new Error("useAuth must be used within an AuthProvider");
	}
	return context;
}
