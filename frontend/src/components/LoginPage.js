import React, { useState } from 'react';
import { useAuth } from '../App';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Alert, AlertDescription } from './ui/alert';
import { toast } from 'sonner';
import { Calendar, Heart, Users, Sparkles, CheckCircle } from 'lucide-react';

const LoginPage = () => {
  const { login, register } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [loginData, setLoginData] = useState({
    email: '',
    password: ''
  });
  
  const [registerData, setRegisterData] = useState({
    email: '',
    password: '',
    fullName: '',
    confirmPassword: ''
  });

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    const result = await login(loginData.email, loginData.password);
    
    if (result.success) {
      toast.success('Welcome back! 🎉');
    } else {
      setError(result.error);
      toast.error(result.error);
    }
    
    setIsLoading(false);
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    if (registerData.password !== registerData.confirmPassword) {
      setError('Passwords do not match');
      setIsLoading(false);
      return;
    }
    
    if (registerData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      setIsLoading(false);
      return;
    }
    
    const result = await register(registerData.email, registerData.password, registerData.fullName);
    
    if (result.success) {
      toast.success('Account created successfully! Welcome! 🎉');
    } else {
      setError(result.error);
      toast.error(result.error);
    }
    
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen flex">
      {/* Left side - Hero Section */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-rose-500 via-pink-500 to-orange-400 relative overflow-hidden">
        <div className="absolute inset-0 bg-black/20" />
        
        {/* Floating elements */}
        <div className="absolute top-20 left-20 animate-float">
          <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-sm">
            <Heart className="w-8 h-8 text-white" />
          </div>
        </div>
        
        <div className="absolute top-40 right-32 animate-float" style={{ animationDelay: '1s' }}>
          <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-sm">
            <Calendar className="w-6 h-6 text-white" />
          </div>
        </div>
        
        <div className="absolute bottom-40 left-32 animate-float" style={{ animationDelay: '2s' }}>
          <div className="w-14 h-14 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-sm">
            <Sparkles className="w-7 h-7 text-white" />
          </div>
        </div>
        
        <div className="relative z-10 flex flex-col justify-center items-start p-16 text-white">
          <h1 className="text-5xl font-bold mb-6 leading-tight">
            Never Miss A
            <span className="block gradient-text bg-gradient-to-r from-yellow-200 to-white bg-clip-text text-transparent">
              Special Moment
            </span>
          </h1>
          
          <p className="text-xl mb-8 text-white/90 max-w-md leading-relaxed">
            Automatically send personalized birthday and anniversary messages to your loved ones with AI-powered customization.
          </p>
          
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-5 h-5 text-green-300" />
              <span className="text-white/90">AI-Generated Personalized Messages</span>
            </div>
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-5 h-5 text-green-300" />
              <span className="text-white/90">WhatsApp & Email Integration</span>
            </div>
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-5 h-5 text-green-300" />
              <span className="text-white/90">Custom Template Management</span>
            </div>
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-5 h-5 text-green-300" />
              <span className="text-white/90">Automated Reminder System</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Right side - Auth Forms */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-rose-500 to-orange-400 rounded-2xl mb-4">
              <Calendar className="w-8 h-8 text-white" />
            </div>
            <h2 className="text-3xl font-bold gradient-text mb-2">ReminderAI</h2>
            <p className="text-gray-600">Your personal celebration assistant</p>
          </div>
          
          <Tabs defaultValue="login" className="w-full">
            <TabsList className="grid w-full grid-cols-2 mb-6">
              <TabsTrigger value="login" data-testid="login-tab">Sign In</TabsTrigger>
              <TabsTrigger value="register" data-testid="register-tab">Sign Up</TabsTrigger>
            </TabsList>
            
            {error && (
              <Alert className="mb-4 border-red-200 bg-red-50">
                <AlertDescription className="text-red-800">{error}</AlertDescription>
              </Alert>
            )}
            
            <TabsContent value="login">
              <Card className="glass border-0 shadow-xl">
                <CardHeader className="text-center pb-4">
                  <CardTitle className="text-2xl font-semibold text-gray-800">Welcome Back</CardTitle>
                  <CardDescription className="text-gray-600">
                    Sign in to your account to continue managing your reminders
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleLogin} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="login-email" className="text-gray-700 font-medium">Email</Label>
                      <Input
                        id="login-email"
                        data-testid="login-email-input"
                        type="email"
                        placeholder="Enter your email"
                        value={loginData.email}
                        onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                        className="form-focus h-12 bg-white/50 border-gray-200"
                        required
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="login-password" className="text-gray-700 font-medium">Password</Label>
                      <Input
                        id="login-password"
                        data-testid="login-password-input"
                        type="password"
                        placeholder="Enter your password"
                        value={loginData.password}
                        onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                        className="form-focus h-12 bg-white/50 border-gray-200"
                        required
                      />
                    </div>
                    
                    <Button
                      type="submit"
                      data-testid="login-submit-button"
                      className="w-full h-12 btn-gradient text-white font-semibold text-lg mt-6"
                      disabled={isLoading}
                    >
                      {isLoading ? (
                        <span className="loading-dots">Signing In</span>
                      ) : (
                        'Sign In'
                      )}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </TabsContent>
            
            <TabsContent value="register">
              <Card className="glass border-0 shadow-xl">
                <CardHeader className="text-center pb-4">
                  <CardTitle className="text-2xl font-semibold text-gray-800">Create Account</CardTitle>
                  <CardDescription className="text-gray-600">
                    Join thousands of users who never miss a special day
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleRegister} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="register-name" className="text-gray-700 font-medium">Full Name</Label>
                      <Input
                        id="register-name"
                        data-testid="register-name-input"
                        type="text"
                        placeholder="Enter your full name"
                        value={registerData.fullName}
                        onChange={(e) => setRegisterData({ ...registerData, fullName: e.target.value })}
                        className="form-focus h-12 bg-white/50 border-gray-200"
                        required
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="register-email" className="text-gray-700 font-medium">Email</Label>
                      <Input
                        id="register-email"
                        data-testid="register-email-input"
                        type="email"
                        placeholder="Enter your email"
                        value={registerData.email}
                        onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                        className="form-focus h-12 bg-white/50 border-gray-200"
                        required
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="register-password" className="text-gray-700 font-medium">Password</Label>
                      <Input
                        id="register-password"
                        data-testid="register-password-input"
                        type="password"
                        placeholder="Create a password (min 6 characters)"
                        value={registerData.password}
                        onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                        className="form-focus h-12 bg-white/50 border-gray-200"
                        required
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="register-confirm-password" className="text-gray-700 font-medium">Confirm Password</Label>
                      <Input
                        id="register-confirm-password"
                        data-testid="register-confirm-password-input"
                        type="password"
                        placeholder="Confirm your password"
                        value={registerData.confirmPassword}
                        onChange={(e) => setRegisterData({ ...registerData, confirmPassword: e.target.value })}
                        className="form-focus h-12 bg-white/50 border-gray-200"
                        required
                      />
                    </div>
                    
                    <Button
                      type="submit"
                      data-testid="register-submit-button"
                      className="w-full h-12 btn-gradient text-white font-semibold text-lg mt-6"
                      disabled={isLoading}
                    >
                      {isLoading ? (
                        <span className="loading-dots">Creating Account</span>
                      ) : (
                        'Create Account'
                      )}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
          
          <div className="text-center mt-6 text-sm text-gray-600">
            <p>By creating an account, you agree to our Terms of Service and Privacy Policy</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;