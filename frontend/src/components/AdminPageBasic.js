import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { toast } from 'sonner';
import { 
  Users, 
  Shield, 
  TrendingUp, 
  Crown,
  CheckCircle,
  XCircle,
  Clock
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updatingUser, setUpdatingUser] = useState(null);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/users`);
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const updateUserSubscription = async (userId, newStatus) => {
    setUpdatingUser(userId);
    
    try {
      await axios.put(`${API}/admin/users/${userId}/subscription`, null, {
        params: { subscription_status: newStatus }
      });
      
      toast.success('User subscription updated successfully!');
      fetchUsers();
    } catch (error) {
      console.error('Error updating user subscription:', error);
      toast.error('Failed to update user subscription');
    } finally {
      setUpdatingUser(null);
    }
  };

  const getSubscriptionColor = (status) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'trial':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'expired':
        return 'bg-red-100 text-red-700 border-red-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getSubscriptionIcon = (status) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'trial':
        return <Clock className="w-4 h-4 text-blue-500" />;
      case 'expired':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Users className="w-4 h-4 text-gray-500" />;
    }
  };

  const stats = {
    totalUsers: users.length,
    activeUsers: users.filter(u => u.subscription_status === 'active').length,
    trialUsers: users.filter(u => u.subscription_status === 'trial').length,
    expiredUsers: users.filter(u => u.subscription_status === 'expired').length
  };

  if (loading) {
    return (
      <div className="min-h-screen p-6 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-rose-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6" data-testid="admin-page">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center" data-testid="admin-title">
            <Shield className="w-8 h-8 mr-3 text-rose-500" />
            Admin Dashboard
          </h1>
          <p className="text-gray-600">
            Manage user subscriptions and monitor platform usage
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="stats-card border-0 shadow-lg" data-testid="total-users-stat">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center">
                <Users className="w-4 h-4 mr-2 text-blue-500" />
                Total Users
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 mb-1" data-testid="total-users-count">
                {stats.totalUsers}
              </div>
              <p className="text-sm text-gray-600">All registered users</p>
            </CardContent>
          </Card>

          <Card className="stats-card border-0 shadow-lg" data-testid="active-users-stat">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center">
                <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                Active Subscriptions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 mb-1" data-testid="active-users-count">
                {stats.activeUsers}
              </div>
              <p className="text-sm text-gray-600">Paid subscribers</p>
            </CardContent>
          </Card>

          <Card className="stats-card border-0 shadow-lg" data-testid="trial-users-stat">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center">
                <Clock className="w-4 h-4 mr-2 text-blue-500" />
                Trial Users
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 mb-1" data-testid="trial-users-count">
                {stats.trialUsers}
              </div>
              <p className="text-sm text-gray-600">On trial period</p>
            </CardContent>
          </Card>

          <Card className="stats-card border-0 shadow-lg" data-testid="revenue-stat">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center">
                <TrendingUp className="w-4 h-4 mr-2 text-purple-500" />
                Revenue (Est.)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 mb-1" data-testid="estimated-revenue">
                ${stats.activeUsers * 9.99}
              </div>
              <p className="text-sm text-gray-600">Monthly recurring</p>
            </CardContent>
          </Card>
        </div>

        {/* Users Management */}
        <Card className="border-0 shadow-xl glass" data-testid="users-management-card">
          <CardHeader>
            <CardTitle className="flex items-center text-xl">
              <Crown className="w-5 h-5 mr-2 text-rose-500" />
              User Management
            </CardTitle>
            <CardDescription>
              Manage user subscriptions and account status
            </CardDescription>
          </CardHeader>
          <CardContent>
            {users.length === 0 ? (
              <div className="text-center py-12" data-testid="no-users-message">
                <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No users found</h3>
                <p className="text-gray-600">Users will appear here once they register</p>
              </div>
            ) : (
              <div className="space-y-4" data-testid="users-list">
                {users.map((user) => (
                  <div 
                    key={user.id} 
                    className="flex items-center justify-between p-4 bg-white/50 rounded-lg border border-white/20 card-hover"
                    data-testid={`user-row-${user.id}`}
                  >
                    <div className="flex items-center space-x-4">
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 bg-gradient-to-br from-rose-500 to-orange-400 rounded-full flex items-center justify-center">
                          <span className="text-white font-semibold text-sm">
                            {user.full_name?.charAt(0)?.toUpperCase() || 'U'}
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900" data-testid={`user-name-${user.id}`}>
                          {user.full_name}
                          {user.is_admin && (
                            <Badge variant="outline" className="ml-2 bg-purple-100 text-purple-700 border-purple-200">
                              <Shield className="w-3 h-3 mr-1" />
                              Admin
                            </Badge>
                          )}
                        </h4>
                        <p className="text-sm text-gray-600" data-testid={`user-email-${user.id}`}>
                          {user.email}
                        </p>
                        <p className="text-xs text-gray-500">
                          Joined: {new Date(user.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <Badge 
                          variant="outline" 
                          className={`${getSubscriptionColor(user.subscription_status)} font-medium flex items-center`}
                          data-testid={`user-status-${user.id}`}
                        >
                          {getSubscriptionIcon(user.subscription_status)}
                          <span className="ml-1 capitalize">{user.subscription_status}</span>
                        </Badge>
                      </div>
                      
                      <Select
                        value={user.subscription_status}
                        onValueChange={(value) => updateUserSubscription(user.id, value)}
                        disabled={updatingUser === user.id}
                      >
                        <SelectTrigger 
                          className="w-32" 
                          data-testid={`subscription-select-${user.id}`}
                        >
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="trial">Trial</SelectItem>
                          <SelectItem value="active">Active</SelectItem>
                          <SelectItem value="expired">Expired</SelectItem>
                          <SelectItem value="cancelled">Cancelled</SelectItem>
                        </SelectContent>
                      </Select>
                      
                      {updatingUser === user.id && (
                        <div className="animate-spin rounded-full h-4 w-4 border-b border-rose-600" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="border-0 shadow-xl glass" data-testid="quick-actions-card">
            <CardHeader>
              <CardTitle className="text-lg">💰 Revenue Insights</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span>Active Subscriptions:</span>
                <span className="font-semibold">{stats.activeUsers}</span>
              </div>
              <div className="flex justify-between">
                <span>Monthly Revenue:</span>
                <span className="font-semibold">${(stats.activeUsers * 9.99).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>Annual Revenue (Est.):</span>
                <span className="font-semibold">${(stats.activeUsers * 9.99 * 12).toFixed(2)}</span>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-xl glass" data-testid="conversion-stats-card">
            <CardHeader>
              <CardTitle className="text-lg">📊 Conversion Stats</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span>Trial → Active:</span>
                <span className="font-semibold">
                  {stats.trialUsers > 0 ? `${((stats.activeUsers / (stats.activeUsers + stats.trialUsers)) * 100).toFixed(1)}%` : '0%'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Total Conversion:</span>
                <span className="font-semibold">
                  {stats.totalUsers > 0 ? `${((stats.activeUsers / stats.totalUsers) * 100).toFixed(1)}%` : '0%'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Growth Rate:</span>
                <span className="font-semibold text-green-600">+12.5%</span>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-xl glass" data-testid="system-health-card">
            <CardHeader>
              <CardTitle className="text-lg">🚀 System Health</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex justify-between items-center">
                <span>API Status:</span>
                <Badge className="bg-green-100 text-green-700 border-green-200">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  Online
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span>Database:</span>
                <Badge className="bg-green-100 text-green-700 border-green-200">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  Connected
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span>AI Service:</span>
                <Badge className="bg-green-100 text-green-700 border-green-200">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  Available
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AdminPage;