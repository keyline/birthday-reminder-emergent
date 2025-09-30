import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../App';
import { Button } from './ui/button';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import { Calendar, Users, FileText, Settings, LogOut, Shield } from 'lucide-react';

const Navbar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  const getInitials = (name) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <nav className="bg-white/80 backdrop-blur-md border-b border-white/20 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/dashboard" className="flex items-center space-x-3" data-testid="navbar-logo">
            <div className="w-8 h-8 bg-gradient-to-br from-rose-500 to-orange-400 rounded-lg flex items-center justify-center">
              <Calendar className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold gradient-text hidden sm:block">ReminderAI</span>
          </Link>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center space-x-1">
            <Link
              to="/dashboard"
              data-testid="nav-dashboard"
              className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                isActive('/dashboard')
                  ? 'bg-rose-100 text-rose-600'
                  : 'text-gray-600 hover:text-rose-600 hover:bg-rose-50'
              }`}
            >
              Dashboard
            </Link>
            <Link
              to="/contacts"
              data-testid="nav-contacts"
              className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                isActive('/contacts')
                  ? 'bg-rose-100 text-rose-600'
                  : 'text-gray-600 hover:text-rose-600 hover:bg-rose-50'
              }`}
            >
              Contacts
            </Link>
            <Link
              to="/templates"
              data-testid="nav-templates"
              className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                isActive('/templates')
                  ? 'bg-rose-100 text-rose-600'
                  : 'text-gray-600 hover:text-rose-600 hover:bg-rose-50'
              }`}
            >
              Templates
            </Link>
            {user?.is_admin && (
              <Link
                to="/admin"
                data-testid="nav-admin"
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                  isActive('/admin')
                    ? 'bg-rose-100 text-rose-600'
                    : 'text-gray-600 hover:text-rose-600 hover:bg-rose-50'
                }`}
              >
                Admin
              </Link>
            )}
          </div>

          {/* User Menu */}
          <div className="flex items-center space-x-4">
            {/* Subscription Status Badge */}
            <div className="hidden sm:block">
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                user?.subscription_status === 'active'
                  ? 'bg-green-100 text-green-700'
                  : user?.subscription_status === 'trial'
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-700'
              }`}>
                {user?.subscription_status?.toUpperCase() || 'FREE'}
              </span>
            </div>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-10 w-10 rounded-full" data-testid="user-menu-trigger">
                  <Avatar className="h-10 w-10">
                    <AvatarImage src="" alt={user?.full_name} />
                    <AvatarFallback className="bg-gradient-to-br from-rose-500 to-orange-400 text-white font-semibold">
                      {getInitials(user?.full_name || 'User')}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56" align="end" forceMount>
                <DropdownMenuLabel className="font-normal">
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium leading-none">{user?.full_name}</p>
                    <p className="text-xs leading-none text-muted-foreground">
                      {user?.email}
                    </p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                
                {/* Mobile Navigation */}
                <div className="md:hidden">
                  <DropdownMenuItem asChild>
                    <Link to="/dashboard" className="flex items-center" data-testid="mobile-nav-dashboard">
                      <Calendar className="mr-2 h-4 w-4" />
                      <span>Dashboard</span>
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link to="/contacts" className="flex items-center" data-testid="mobile-nav-contacts">
                      <Users className="mr-2 h-4 w-4" />
                      <span>Contacts</span>
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link to="/templates" className="flex items-center" data-testid="mobile-nav-templates">
                      <FileText className="mr-2 h-4 w-4" />
                      <span>Templates</span>
                    </Link>
                  </DropdownMenuItem>
                  {user?.is_admin && (
                    <DropdownMenuItem asChild>
                      <Link to="/admin" className="flex items-center" data-testid="mobile-nav-admin">
                        <Shield className="mr-2 h-4 w-4" />
                        <span>Admin</span>
                      </Link>
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuSeparator />
                </div>
                
                <DropdownMenuItem asChild>
                  <Link to="/settings" className="flex items-center cursor-pointer">
                    <Settings className="mr-2 h-4 w-4" />
                    <span>Settings</span>
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem 
                  className="cursor-pointer text-red-600 focus:text-red-600" 
                  onClick={logout}
                  data-testid="logout-button"
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Log out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;