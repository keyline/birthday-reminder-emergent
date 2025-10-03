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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Checkbox } from './ui/checkbox';
import { Textarea } from './ui/textarea';
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
  AlertCircle,
  Palette,
  Image,
  Eye,
  MessageSquare,
  Volume2,
  Copy
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
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    whatsapp: '',
    birthday: '',
    anniversary_date: '',
    message_tone: 'normal',
    whatsapp_image: '',
    email_image: ''
  });
  const [selectedContacts, setSelectedContacts] = useState([]);
  const [showBulkActions, setShowBulkActions] = useState(false);
  const [bulkTone, setBulkTone] = useState('normal');
  const [messagePreview, setMessagePreview] = useState(null);
  const [showMessageDialog, setShowMessageDialog] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [viewMode, setViewMode] = useState('card'); // 'card' or 'grid'
  const [filterBy, setFilterBy] = useState('all'); // 'all', 'birthday', 'anniversary', 'both'
  const [sortBy, setSortBy] = useState('name'); // 'name', 'created', 'birthday', 'anniversary'
  const [messageDialogOpen, setMessageDialogOpen] = useState(false);
  const [selectedContact, setSelectedContact] = useState(null);
  const [selectedMessageType, setSelectedMessageType] = useState(''); // 'whatsapp' or 'email'
  const [selectedOccasion, setSelectedOccasion] = useState(''); // 'birthday' or 'anniversary'
  const [customMessage, setCustomMessage] = useState('');
  const [generatingAIMessage, setGeneratingAIMessage] = useState(false);
  const [sendingTestMessage, setSendingTestMessage] = useState(false);

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
      anniversary_date: contact.anniversary_date || '',
      message_tone: contact.message_tone || 'normal',
      whatsapp_image: contact.whatsapp_image || '',
      email_image: contact.email_image || ''
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
      anniversary_date: '',
      message_tone: 'normal',
      whatsapp_image: '',
      email_image: ''
    });
    setEditingContact(null);
  };

  // Excel Upload Functions
  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploading(true);
    setUploadProgress(0);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const response = await axios.post(`${API}/contacts/bulk-upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      const result = response.data;
      setUploadResult(result);

      if (result.successful_imports > 0) {
        toast.success(`Successfully imported ${result.successful_imports} contacts!`);
        fetchContacts(); // Refresh the contacts list
      }

      if (result.failed_imports > 0) {
        toast.warning(`${result.failed_imports} contacts failed to import. Check the results for details.`);
      }

    } catch (error) {
      console.error('Error uploading file:', error);
      toast.error(error.response?.data?.detail || 'Failed to upload file');
      setUploadResult({
        total_rows: 0,
        successful_imports: 0,
        failed_imports: 1,
        errors: [error.response?.data?.detail || 'Upload failed'],
        imported_contacts: []
      });
    } finally {
      setUploading(false);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    maxFiles: 1
  });

  const downloadTemplate = () => {
    // Create a sample Excel template with new format
    const templateData = [
      ['name', 'birthday', 'anniversary', 'email', 'whatsapp'],
      ['John Doe', '15-05', '', 'john@example.com', '+1234567890'],
      ['Jane Smith', '', '20-09', 'jane@example.com', ''],
      ['Bob Johnson', '03-12-1985', '14-07-2010', '', '+9876543210'],
      ['Alice Brown', '25-08', '', 'alice@example.com', '+1122334455'],
      ['Mike Wilson', '10-11', '05-06', 'mike@example.com', '+5566778899']
    ];

    const csvContent = templateData.map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'contacts_template.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    toast.success('Template downloaded! You can open it in Excel and save as .xlsx format.');
  };

  const resetUpload = () => {
    setUploadResult(null);
    setUploadProgress(0);
    setUploading(false);
  };

  const messageTonesOptions = [
    { value: 'normal', label: 'Normal', description: 'Warm and friendly' },
    { value: 'business', label: 'Business', description: 'Professional and courteous' },
    { value: 'formal', label: 'Formal', description: 'Elegant and sophisticated' },
    { value: 'informal', label: 'Informal', description: 'Casual and relaxed' },
    { value: 'funny', label: 'Funny', description: 'Light-hearted and amusing' },
    { value: 'casual', label: 'Casual', description: 'Easy-going and laid-back' }
  ];

  const handleBulkToneUpdate = async () => {
    if (selectedContacts.length === 0) {
      toast.error('Please select contacts first');
      return;
    }

    try {
      const response = await axios.put(`${API}/contacts/bulk-tone-update`, {
        contact_ids: selectedContacts,
        message_tone: bulkTone
      });

      toast.success(`Updated tone for ${response.data.updated_count} contacts`);
      fetchContacts();
      setSelectedContacts([]);
      setShowBulkActions(false);
    } catch (error) {
      console.error('Error updating bulk tone:', error);
      toast.error('Failed to update contact tones');
    }
  };

  const handleContactSelect = (contactId) => {
    setSelectedContacts(prev => {
      const newSelected = prev.includes(contactId) 
        ? prev.filter(id => id !== contactId)
        : [...prev, contactId];
      
      setShowBulkActions(newSelected.length > 0);
      return newSelected;
    });
  };

  const generateMessagePreview = async (contact, occasion, messageType) => {
    try {
      const response = await axios.post(`${API}/generate-message-preview`, null, {
        params: {
          contact_id: contact.id,
          occasion: occasion,
          message_type: messageType
        }
      });

      setMessagePreview(response.data);
      setShowMessageDialog(true);
    } catch (error) {
      console.error('Error generating message preview:', error);
      toast.error('Failed to generate message preview');
    }
  };

  const uploadImage = async (file, imageType) => {
    setUploadingImage(true);
    
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API}/upload-image`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      return response.data.image_url;
    } catch (error) {
      console.error('Error uploading image:', error);
      toast.error('Failed to upload image');
      return null;
    } finally {
      setUploadingImage(false);
    }
  };

  const handleImageUpload = async (event, imageType) => {
    const file = event.target.files[0];
    if (!file) return;

    const imageUrl = await uploadImage(file, imageType);
    if (imageUrl) {
      setFormData(prev => ({
        ...prev,
        [imageType]: imageUrl
      }));
      toast.success('Image uploaded successfully');
    }
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
          
          <div className="flex gap-3">
            {/* Bulk Upload Dialog */}
            <Dialog open={isUploadDialogOpen} onOpenChange={setIsUploadDialogOpen}>
              <DialogTrigger asChild>
                <Button 
                  variant="outline" 
                  className="bg-white/80 border-gray-200 hover:bg-white hover:shadow-md"
                  onClick={resetUpload}
                  data-testid="bulk-upload-button"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  Bulk Upload
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-2xl">
                <DialogHeader>
                  <DialogTitle className="flex items-center" data-testid="upload-dialog-title">
                    <FileSpreadsheet className="w-5 h-5 mr-2 text-green-600" />
                    Bulk Upload Contacts
                  </DialogTitle>
                  <DialogDescription>
                    Upload an Excel file (.xlsx or .xls) with your contacts data
                  </DialogDescription>
                </DialogHeader>
                
                {!uploadResult ? (
                  <div className="space-y-6">
                    {/* Upload Instructions */}
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        <strong>Excel Format Requirements:</strong>
                        <ul className="mt-2 space-y-1 text-sm">
                          <li>• Column 1: <strong>name</strong> (required)</li>
                          <li>• Column 2: <strong>birthday</strong> (optional, format: DD-MM or DD-MM-YYYY)</li>
                          <li>• Column 3: <strong>anniversary</strong> (optional, format: DD-MM or DD-MM-YYYY)</li>
                          <li>• Column 4: <strong>email</strong> (optional, valid email format)</li>
                          <li>• Column 5: <strong>whatsapp</strong> (optional, phone number)</li>
                          <li>• <strong>Contact Info:</strong> At least one of email OR WhatsApp is required</li>
                          <li>• <strong>Dates:</strong> At least one of birthday OR anniversary is required</li>
                          <li>• <strong>Duplicates:</strong> Email/WhatsApp checked against your existing contacts</li>
                        </ul>
                      </AlertDescription>
                    </Alert>

                    {/* Download Template Button */}
                    <div className="flex justify-center">
                      <Button
                        variant="outline"
                        onClick={downloadTemplate}
                        className="mb-4"
                        data-testid="download-template-button"
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Download Template
                      </Button>
                    </div>

                    {/* Upload Area */}
                    <div
                      {...getRootProps()}
                      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                        isDragActive
                          ? 'border-rose-400 bg-rose-50'
                          : 'border-gray-300 hover:border-rose-400 hover:bg-rose-50'
                      }`}
                      data-testid="file-drop-zone"
                    >
                      <input {...getInputProps()} />
                      <FileSpreadsheet className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                      {isDragActive ? (
                        <p className="text-rose-600 font-medium">Drop your Excel file here...</p>
                      ) : (
                        <div>
                          <p className="text-gray-600 mb-2">
                            Drag and drop your Excel file here, or{' '}
                            <span className="text-rose-600 font-medium">browse</span>
                          </p>
                          <p className="text-sm text-gray-500">Supports .xlsx and .xls files</p>
                        </div>
                      )}
                    </div>

                    {/* Upload Progress */}
                    {uploading && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>Uploading and processing...</span>
                          <span>{uploadProgress}%</span>
                        </div>
                        <Progress value={uploadProgress} className="w-full" />
                      </div>
                    )}
                  </div>
                ) : (
                  /* Upload Results */
                  <div className="space-y-4">
                    <div className="grid grid-cols-3 gap-4">
                      <Card className="text-center p-4">
                        <div className="text-2xl font-bold text-blue-600">{uploadResult.total_rows}</div>
                        <div className="text-sm text-gray-600">Total Rows</div>
                      </Card>
                      <Card className="text-center p-4">
                        <div className="text-2xl font-bold text-green-600 flex items-center justify-center">
                          <CheckCircle className="w-6 h-6 mr-1" />
                          {uploadResult.successful_imports}
                        </div>
                        <div className="text-sm text-gray-600">Imported</div>
                      </Card>
                      <Card className="text-center p-4">
                        <div className="text-2xl font-bold text-red-600 flex items-center justify-center">
                          <XCircle className="w-6 h-6 mr-1" />
                          {uploadResult.failed_imports}
                        </div>
                        <div className="text-sm text-gray-600">Failed</div>
                      </Card>
                    </div>

                    {uploadResult.errors.length > 0 && (
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Import Errors:</h4>
                        <div className="max-h-40 overflow-y-auto bg-red-50 rounded-lg p-3">
                          <ul className="space-y-1 text-sm text-red-700">
                            {uploadResult.errors.map((error, index) => (
                              <li key={index}>• {error}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    )}

                    <div className="flex justify-end space-x-2">
                      <Button
                        variant="outline"
                        onClick={resetUpload}
                        data-testid="upload-another-button"
                      >
                        Upload Another File
                      </Button>
                      <Button
                        onClick={() => setIsUploadDialogOpen(false)}
                        className="btn-gradient"
                        data-testid="close-upload-dialog-button"
                      >
                        Close
                      </Button>
                    </div>
                  </div>
                )}
              </DialogContent>
            </Dialog>

            {/* Add Contact Dialog */}
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

        {/* Contacts Grid - Simplified for now */}
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
            {filteredContacts.map((contact) => (
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
                  
                  {/* Action Icons */}
                  <div className="flex justify-center space-x-3 pt-3 border-t border-gray-100">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleMessageEdit(contact, 'whatsapp')}
                      className="h-10 px-3 hover:bg-green-50 hover:text-green-600 hover:border-green-300"
                      title="Edit WhatsApp Message"
                      data-testid={`whatsapp-message-${contact.id}`}
                    >
                      <MessageSquare className="w-4 h-4 mr-1" />
                      <span className="text-xs">WhatsApp</span>
                    </Button>
                    
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleMessageEdit(contact, 'email')}
                      className="h-10 px-3 hover:bg-blue-50 hover:text-blue-600 hover:border-blue-300"
                      title="Edit Email Message"
                      data-testid={`email-message-${contact.id}`}
                    >
                      <Mail className="w-4 h-4 mr-1" />
                      <span className="text-xs">Email</span>
                    </Button>
                    
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleSendTest(contact)}
                      className="h-10 px-3 hover:bg-purple-50 hover:text-purple-600 hover:border-purple-300"
                      title="Send Test Messages"
                      data-testid={`test-message-${contact.id}`}
                    >
                      <Volume2 className="w-4 h-4 mr-1" />
                      <span className="text-xs">Test</span>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
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