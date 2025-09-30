import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useDropzone } from 'react-dropzone';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Alert, AlertDescription } from './ui/alert';
import { toast } from 'sonner';
import { 
  Plus, 
  Edit, 
  Trash2, 
  Users, 
  Mail, 
  Phone, 
  Calendar, 
  Heart,
  Search,
  Gift,
  Sparkles,
  Upload,
  FileSpreadsheet,
  Download,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ContactsPage = () => {
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingContact, setEditingContact] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [generatingMessage, setGeneratingMessage] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    whatsapp: '',
    birthday: '',
    anniversary_date: ''
  });

  useEffect(() => {
    fetchContacts();
  }, []);

  const fetchContacts = async () => {
    try {
      const response = await axios.get(`${API}/contacts`);
      setContacts(response.data);
    } catch (error) {
      console.error('Error fetching contacts:', error);
      toast.error('Failed to load contacts');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const contactData = {
        ...formData,
        email: formData.email || null,
        whatsapp: formData.whatsapp || null,
        birthday: formData.birthday || null,
        anniversary_date: formData.anniversary_date || null
      };

      if (editingContact) {
        await axios.put(`${API}/contacts/${editingContact.id}`, contactData);
        toast.success('Contact updated successfully!');
      } else {
        await axios.post(`${API}/contacts`, contactData);
        toast.success('Contact added successfully!');
      }
      
      resetForm();
      setIsDialogOpen(false);
      fetchContacts();
    } catch (error) {
      console.error('Error saving contact:', error);
      toast.error(error.response?.data?.detail || 'Failed to save contact');
    }
  };

  const handleEdit = (contact) => {
    setEditingContact(contact);
    setFormData({
      name: contact.name || '',
      email: contact.email || '',
      whatsapp: contact.whatsapp || '',
      birthday: contact.birthday || '',
      anniversary_date: contact.anniversary_date || ''
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (contactId, contactName) => {
    if (window.confirm(`Are you sure you want to delete ${contactName}?`)) {
      try {
        await axios.delete(`${API}/contacts/${contactId}`);
        toast.success('Contact deleted successfully!');
        fetchContacts();
      } catch (error) {
        console.error('Error deleting contact:', error);
        toast.error('Failed to delete contact');
      }
    }
  };

  const generateMessage = async (contact, occasion) => {
    setGeneratingMessage(`${contact.id}-${occasion}`);
    
    try {
      const response = await axios.post(`${API}/generate-message`, {
        contact_name: contact.name,
        occasion: occasion,
        relationship: 'friend',
        tone: 'warm'
      });
      
      toast.success(`Generated ${occasion} message for ${contact.name}!`, {
        description: response.data.message,
        duration: 10000
      });
    } catch (error) {
      console.error('Error generating message:', error);
      toast.error('Failed to generate message');
    } finally {
      setGeneratingMessage(null);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      email: '',
      whatsapp: '',
      birthday: '',
      anniversary_date: ''
    });
    setEditingContact(null);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Not set';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getUpcomingEvents = (contact) => {
    const events = [];
    const today = new Date();
    
    if (contact.birthday) {
      const birthday = new Date(contact.birthday);
      const thisYearBirthday = new Date(today.getFullYear(), birthday.getMonth(), birthday.getDate());
      if (thisYearBirthday < today) {
        thisYearBirthday.setFullYear(today.getFullYear() + 1);
      }
      const daysUntil = Math.ceil((thisYearBirthday - today) / (1000 * 60 * 60 * 24));
      if (daysUntil <= 30) {
        events.push({ type: 'birthday', days: daysUntil });
      }
    }
    
    if (contact.anniversary_date) {
      const anniversary = new Date(contact.anniversary_date);
      const thisYearAnniversary = new Date(today.getFullYear(), anniversary.getMonth(), anniversary.getDate());
      if (thisYearAnniversary < today) {
        thisYearAnniversary.setFullYear(today.getFullYear() + 1);
      }
      const daysUntil = Math.ceil((thisYearAnniversary - today) / (1000 * 60 * 60 * 24));
      if (daysUntil <= 30) {
        events.push({ type: 'anniversary', days: daysUntil });
      }
    }
    
    return events.sort((a, b) => a.days - b.days);
  };

  const filteredContacts = contacts.filter(contact =>
    contact.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (contact.email && contact.email.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  if (loading) {
    return (
      <div className="min-h-screen p-6 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-rose-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6" data-testid="contacts-page">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2" data-testid="contacts-title">
              My Contacts
            </h1>
            <p className="text-gray-600">
              Manage the people you want to celebrate with
            </p>
          </div>
          
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button 
                className="btn-gradient" 
                onClick={resetForm}
                data-testid="add-contact-button"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Contact
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle data-testid="contact-dialog-title">
                  {editingContact ? 'Edit Contact' : 'Add New Contact'}
                </DialogTitle>
                <DialogDescription>
                  {editingContact 
                    ? 'Update the contact information below.'
                    : 'Add a new person to your celebration list.'
                  }
                </DialogDescription>
              </DialogHeader>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name *</Label>
                  <Input
                    id="name"
                    data-testid="contact-name-input"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Enter full name"
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    data-testid="contact-email-input"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="Enter email address"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="whatsapp">WhatsApp Number</Label>
                  <Input
                    id="whatsapp"
                    data-testid="contact-whatsapp-input"
                    value={formData.whatsapp}
                    onChange={(e) => setFormData({ ...formData, whatsapp: e.target.value })}
                    placeholder="Enter WhatsApp number"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="birthday">Birthday</Label>
                  <Input
                    id="birthday"
                    data-testid="contact-birthday-input"
                    type="date"
                    value={formData.birthday}
                    onChange={(e) => setFormData({ ...formData, birthday: e.target.value })}
                    className="date-picker"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="anniversary">Anniversary Date</Label>
                  <Input
                    id="anniversary"
                    data-testid="contact-anniversary-input"
                    type="date"
                    value={formData.anniversary_date}
                    onChange={(e) => setFormData({ ...formData, anniversary_date: e.target.value })}
                    className="date-picker"
                  />
                </div>
                
                <div className="flex justify-end space-x-2 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setIsDialogOpen(false)}
                    data-testid="cancel-contact-button"
                  >
                    Cancel
                  </Button>
                  <Button 
                    type="submit" 
                    className="btn-gradient"
                    data-testid="save-contact-button"
                  >
                    {editingContact ? 'Update Contact' : 'Add Contact'}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Search */}
        <div className="mb-6">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              data-testid="contacts-search-input"
              placeholder="Search contacts..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 bg-white/50"
            />
          </div>
        </div>

        {/* Contacts Grid */}
        {filteredContacts.length === 0 ? (
          <div className="text-center py-16" data-testid="no-contacts-message">
            <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {searchTerm ? 'No contacts found' : 'No contacts yet'}
            </h3>
            <p className="text-gray-600 mb-6">
              {searchTerm 
                ? 'Try adjusting your search terms'
                : 'Add your first contact to start celebrating special moments!'
              }
            </p>
            {!searchTerm && (
              <Button 
                className="btn-gradient" 
                onClick={() => {
                  resetForm();
                  setIsDialogOpen(true);
                }}
                data-testid="add-first-contact-button"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Your First Contact
              </Button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="contacts-grid">
            {filteredContacts.map((contact) => {
              const upcomingEvents = getUpcomingEvents(contact);
              
              return (
                <Card 
                  key={contact.id} 
                  className="card-hover glass border-0 shadow-lg"
                  data-testid={`contact-card-${contact.id}`}
                >
                  <CardHeader className="pb-3">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <CardTitle className="text-lg font-semibold text-gray-900 mb-1" data-testid={`contact-name-${contact.id}`}>
                          {contact.name}
                        </CardTitle>
                        
                        {/* Upcoming Events */}
                        {upcomingEvents.length > 0 && (
                          <div className="flex flex-wrap gap-1 mb-2">
                            {upcomingEvents.map((event, index) => (
                              <Badge 
                                key={index}
                                variant="outline" 
                                className={`text-xs ${
                                  event.type === 'birthday' 
                                    ? 'bg-rose-50 text-rose-700 border-rose-200'
                                    : 'bg-pink-50 text-pink-700 border-pink-200'
                                }`}
                                data-testid={`upcoming-event-${contact.id}-${index}`}
                              >
                                {event.type === 'birthday' ? (
                                  <Gift className="w-3 h-3 mr-1" />
                                ) : (
                                  <Heart className="w-3 h-3 mr-1" />
                                )}
                                {event.days === 0 ? 'Today!' : `${event.days}d`}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                      
                      <div className="flex space-x-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleEdit(contact)}
                          className="h-8 w-8 p-0 hover:bg-blue-50 hover:text-blue-600"
                          data-testid={`edit-contact-${contact.id}`}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleDelete(contact.id, contact.name)}
                          className="h-8 w-8 p-0 hover:bg-red-50 hover:text-red-600"
                          data-testid={`delete-contact-${contact.id}`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  
                  <CardContent className="space-y-3">
                    {/* Contact Info */}
                    <div className="space-y-2 text-sm">
                      {contact.email && (
                        <div className="flex items-center text-gray-600" data-testid={`contact-email-${contact.id}`}>
                          <Mail className="w-4 h-4 mr-2 text-gray-400" />
                          <span className="truncate">{contact.email}</span>
                        </div>
                      )}
                      
                      {contact.whatsapp && (
                        <div className="flex items-center text-gray-600" data-testid={`contact-whatsapp-${contact.id}`}>
                          <Phone className="w-4 h-4 mr-2 text-gray-400" />
                          <span>{contact.whatsapp}</span>
                        </div>
                      )}
                      
                      {contact.birthday && (
                        <div className="flex items-center text-gray-600" data-testid={`contact-birthday-${contact.id}`}>
                          <Gift className="w-4 h-4 mr-2 text-gray-400" />
                          <span>Birthday: {formatDate(contact.birthday)}</span>
                        </div>
                      )}
                      
                      {contact.anniversary_date && (
                        <div className="flex items-center text-gray-600" data-testid={`contact-anniversary-${contact.id}`}>
                          <Heart className="w-4 h-4 mr-2 text-gray-400" />
                          <span>Anniversary: {formatDate(contact.anniversary_date)}</span>
                        </div>
                      )}
                    </div>
                    
                    {/* AI Message Generation */}
                    <div className="pt-3 border-t border-gray-100">
                      <p className="text-xs text-gray-500 mb-2">Generate AI message:</p>
                      <div className="flex space-x-2">
                        {contact.birthday && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => generateMessage(contact, 'birthday')}
                            disabled={generatingMessage === `${contact.id}-birthday`}
                            className="flex-1 text-xs h-7 bg-rose-50 hover:bg-rose-100 text-rose-700 border-rose-200"
                            data-testid={`generate-birthday-message-${contact.id}`}
                          >
                            {generatingMessage === `${contact.id}-birthday` ? (
                              <div className="animate-spin rounded-full h-3 w-3 border-b border-rose-600" />
                            ) : (
                              <>
                                <Gift className="w-3 h-3 mr-1" />
                                Birthday
                              </>
                            )}
                          </Button>
                        )}
                        
                        {contact.anniversary_date && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => generateMessage(contact, 'anniversary')}
                            disabled={generatingMessage === `${contact.id}-anniversary`}
                            className="flex-1 text-xs h-7 bg-pink-50 hover:bg-pink-100 text-pink-700 border-pink-200"
                            data-testid={`generate-anniversary-message-${contact.id}`}
                          >
                            {generatingMessage === `${contact.id}-anniversary` ? (
                              <div className="animate-spin rounded-full h-3 w-3 border-b border-pink-600" />
                            ) : (
                              <>
                                <Heart className="w-3 h-3 mr-1" />
                                Anniversary
                              </>
                            )}
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
        
        {/* Stats Footer */}
        {filteredContacts.length > 0 && (
          <div className="mt-8 text-center" data-testid="contacts-stats">
            <p className="text-gray-600">
              Showing {filteredContacts.length} of {contacts.length} contacts
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ContactsPage;