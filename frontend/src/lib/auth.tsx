import { createContext, useContext, useState, ReactNode } from "react";
import { clearToken, login as apiLogin, register as apiRegister, setToken } from "./api";

interface AuthContextValue {
  isAuthenticated: boolean;
  email: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [email, setEmail] = useState<string | null>(() => localStorage.getItem("studymate_email"));

  async function login(emailInput: string, password: string) {
    await apiLogin(emailInput, password);
    localStorage.setItem("studymate_email", emailInput);
    setEmail(emailInput);
  }

  async function register(emailInput: string, password: string, fullName?: string) {
    await apiRegister(emailInput, password, fullName);
    await login(emailInput, password);
  }

  function logout() {
    clearToken();
    localStorage.removeItem("studymate_email");
    setEmail(null);
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated: !!email, email, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

// Re-exported so components don't need to import setToken from api.ts directly
export { setToken };
