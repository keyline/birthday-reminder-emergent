import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Label } from './ui/label';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from './ui/dialog';
import { toast } from 'sonner';
import { Users, Mail, Phone, Edit, CreditCard, LogOut, Shield } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminDashboard() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingUser, setEditingUser] = useState(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [subscriptionDialogOpen, setSubscriptionDialogOpen] = useState(false);
  const [adminInfo, setAdminInfo] = useState(null);

  // Form states
  const [editForm, setEditForm] = useState({
    full_name: '',
    email: '',
    phone_number: ''
  });

  const [subscriptionForm, setSubscriptionForm] = useState({
    subscription_status: '',
    whatsapp_credits: 0,
    email_credits: 0,
    unlimited_whatsapp: false,
    unlimited_email: false
  });

  useEffect(() => {
    // Get admin info
    const info = localStorage.getItem('admin_info');
    if (info) {
      setAdminInfo(JSON.parse(info));
    }

    // Setup axios interceptor with admin token
    const token = localStorage.getItem('admin_token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }

    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/admin/users`);
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to load users:', error);
      toast.error('Failed to load users');
      
      // If unauthorized, redirect to admin login
      if (error.response?.status === 401) {
        handleLogout();
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_info');
    delete axios.defaults.headers.common['Authorization'];
    window.location.href = '/admin/login';
  };

  const openEditDialog = (user) => {
    setEditingUser(user);
    setEditForm({
      full_name: user.full_name,
      email: user.email,
      phone_number: user.phone_number || ''
    });
    setEditDialogOpen(true);
  };

  const openSubscriptionDialog = (user) => {
    setEditingUser(user);
    setSubscriptionForm({
      subscription_status: user.subscription_status,
      whatsapp_credits: user.whatsapp_credits,
      email_credits: user.email_credits,
      unlimited_whatsapp: user.unlimited_whatsapp,
      unlimited_email: user.unlimited_email
    });
    setSubscriptionDialogOpen(true);
  };

  const handleUpdateUser = async () => {
    try {
      await axios.put(`${API}/admin/users/${editingUser.id}`, editForm);
      toast.success('User updated successfully');
      setEditDialogOpen(false);
      loadUsers();
    } catch (error) {
      console.error('Failed to update user:', error);
      const errorMsg = error.response?.data?.detail || 'Failed to update user';
      toast.error(errorMsg);
    }
  };

  const handleUpdateSubscription = async () => {
    try {
      await axios.put(`${API}/admin/users/${editingUser.id}/subscription`, subscriptionForm);
      toast.success('Subscription updated successfully');
      setSubscriptionDialogOpen(false);
      loadUsers();
    } catch (error) {
      console.error('Failed to update subscription:', error);
      const errorMsg = error.response?.data?.detail || 'Failed to update subscription';
      toast.error(errorMsg);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <Shield className="h-8 w-8 text-purple-400" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">Admin Dashboard</h1>
              <p className="text-slate-400">Welcome, {adminInfo?.username}</p>
            </div>
          </div>
          <Button
            onClick={handleLogout}
            variant="outline"
            className="border-red-500/50 text-red-400 hover:bg-red-500/10"
          >
            <LogOut className="mr-2 h-4 w-4" />
            Logout
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card className="bg-slate-800/50 border-purple-500/20">
          <CardHeader>
            <CardTitle className="text-white flex items-center">
              <Users className="mr-2 h-5 w-5 text-purple-400" />
              Total Users
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-purple-400">{users.length}</p>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-purple-500/20">
          <CardHeader>
            <CardTitle className="text-white flex items-center">
              <Mail className="mr-2 h-5 w-5 text-green-400" />
              Total Contacts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-green-400">
              {users.reduce((sum, user) => sum + user.contact_count, 0)}
            </p>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-purple-500/20">
          <CardHeader>
            <CardTitle className="text-white flex items-center">
              <CreditCard className="mr-2 h-5 w-5 text-blue-400" />
              Active Subscriptions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-blue-400">
              {users.filter(u => u.subscription_status === 'active').length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Users Table */}
      <div className="max-w-7xl mx-auto">
        <Card className="bg-slate-800/50 border-purple-500/20">
          <CardHeader>
            <CardTitle className="text-white">All Users</CardTitle>
            <CardDescription className="text-slate-400">
              Manage users, their details, and subscriptions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left p-3 text-slate-300 font-semibold">Name</th>
                    <th className="text-left p-3 text-slate-300 font-semibold">Email</th>
                    <th className="text-left p-3 text-slate-300 font-semibold">Phone</th>
                    <th className="text-center p-3 text-slate-300 font-semibold">Contacts</th>
                    <th className="text-center p-3 text-slate-300 font-semibold">Status</th>
                    <th className="text-center p-3 text-slate-300 font-semibold">WA Credits</th>
                    <th className="text-center p-3 text-slate-300 font-semibold">Email Credits</th>
                    <th className="text-center p-3 text-slate-300 font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                      <td className="p-3 text-slate-200">{user.full_name}</td>
                      <td className="p-3 text-slate-400 text-sm">{user.email}</td>
                      <td className="p-3 text-slate-400 text-sm">{user.phone_number || '-'}</td>
                      <td className="p-3 text-center text-purple-400 font-semibold">{user.contact_count}</td>
                      <td className="p-3 text-center">
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                          user.subscription_status === 'active' ? 'bg-green-500/20 text-green-400' :
                          user.subscription_status === 'trial' ? 'bg-blue-500/20 text-blue-400' :
                          'bg-red-500/20 text-red-400'
                        }`}>
                          {user.subscription_status}
                        </span>
                      </td>
                      <td className="p-3 text-center text-slate-300">
                        {user.unlimited_whatsapp ? '∞' : user.whatsapp_credits}
                      </td>
                      <td className="p-3 text-center text-slate-300">
                        {user.unlimited_email ? '∞' : user.email_credits}
                      </td>
                      <td className="p-3">
                        <div className="flex items-center justify-center space-x-2">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => openEditDialog(user)}
                            className="text-blue-400 hover:text-blue-300 hover:bg-blue-500/10"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => openSubscriptionDialog(user)}
                            className="text-green-400 hover:text-green-300 hover:bg-green-500/10"
                          >
                            <CreditCard className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Edit User Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="bg-slate-800 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white">Edit User Details</DialogTitle>
            <DialogDescription className="text-slate-400">
              Update user information
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="edit_name" className="text-slate-200">Full Name</Label>
              <Input
                id="edit_name"
                value={editForm.full_name}
                onChange={(e) => setEditForm({...editForm, full_name: e.target.value})}
                className="bg-slate-700 border-slate-600 text-white"
              />
            </div>
            <div>
              <Label htmlFor="edit_email" className="text-slate-200">Email</Label>
              <Input
                id="edit_email"
                type="email"
                value={editForm.email}
                onChange={(e) => setEditForm({...editForm, email: e.target.value})}
                className="bg-slate-700 border-slate-600 text-white"
              />
            </div>
            <div>
              <Label htmlFor="edit_phone" className="text-slate-200">Phone Number (10 digits)</Label>
              <Input
                id="edit_phone"
                value={editForm.phone_number}
                onChange={(e) => setEditForm({...editForm, phone_number: e.target.value})}
                className="bg-slate-700 border-slate-600 text-white"
                placeholder="9876543210"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)} className="border-slate-600 text-slate-300">
              Cancel
            </Button>
            <Button onClick={handleUpdateUser} className="bg-purple-500 hover:bg-purple-600">
              Update User
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Subscription Dialog */}
      <Dialog open={subscriptionDialogOpen} onOpenChange={setSubscriptionDialogOpen}>
        <DialogContent className="bg-slate-800 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white">Manage Subscription & Credits</DialogTitle>
            <DialogDescription className="text-slate-400">
              Update user subscription and credits
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="sub_status" className="text-slate-200">Subscription Status</Label>
              <select
                id="sub_status"
                value={subscriptionForm.subscription_status}
                onChange={(e) => setSubscriptionForm({...subscriptionForm, subscription_status: e.target.value})}
                className="w-full p-2 bg-slate-700 border-slate-600 text-white rounded-md"
              >
                <option value="trial">Trial</option>
                <option value="active">Active</option>
                <option value="expired">Expired</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
            <div>
              <Label htmlFor="wa_credits" className="text-slate-200">WhatsApp Credits</Label>
              <Input
                id="wa_credits"
                type="number"
                value={subscriptionForm.whatsapp_credits}
                onChange={(e) => setSubscriptionForm({...subscriptionForm, whatsapp_credits: parseInt(e.target.value)})}
                className="bg-slate-700 border-slate-600 text-white"
              />
              <div className="flex items-center space-x-2 mt-2">
                <input
                  type="checkbox"
                  id="unlimited_wa"
                  checked={subscriptionForm.unlimited_whatsapp}
                  onChange={(e) => setSubscriptionForm({...subscriptionForm, unlimited_whatsapp: e.target.checked})}
                  className="rounded"
                />
                <Label htmlFor="unlimited_wa" className="text-slate-300 text-sm">Unlimited WhatsApp</Label>
              </div>
            </div>
            <div>
              <Label htmlFor="email_credits" className="text-slate-200">Email Credits</Label>
              <Input
                id="email_credits"
                type="number"
                value={subscriptionForm.email_credits}
                onChange={(e) => setSubscriptionForm({...subscriptionForm, email_credits: parseInt(e.target.value)})}
                className="bg-slate-700 border-slate-600 text-white"
              />
              <div className="flex items-center space-x-2 mt-2">
                <input
                  type="checkbox"
                  id="unlimited_email"
                  checked={subscriptionForm.unlimited_email}
                  onChange={(e) => setSubscriptionForm({...subscriptionForm, unlimited_email: e.target.checked})}
                  className="rounded"
                />
                <Label htmlFor="unlimited_email" className="text-slate-300 text-sm">Unlimited Email</Label>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSubscriptionDialogOpen(false)} className="border-slate-600 text-slate-300">
              Cancel
            </Button>
            <Button onClick={handleUpdateSubscription} className="bg-green-500 hover:bg-green-600">
              Update Subscription
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
