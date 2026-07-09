// ─── Mock Candidates ─────────────────────────────────────────────────────────
export const mockCandidates = [
  {
    id: '1', name: 'Rahul Sharma', email: 'rahul.sharma@gmail.com',
    phone: '+91 98765 43210', college: 'IIT Bombay', cgpa: '9.2',
    role: 'Frontend Developer', status: 'completed',
    appliedDate: '2026-06-05', interviewDate: '2026-07-15',
    salary: '₹25,000/month', joiningDate: '2024-02-01',
    skills: ['React', 'JavaScript', 'Tailwind CSS'],
    resumeScore: 92, avatar: null,
    address: '12, MG Road, Mumbai, Maharashtra',
    bank: 'HDFC Bank - XXXX1234', pan: 'ABCDE1234F', aadhaar: 'XXXX XXXX 5678',
  },
  {
    id: '2', name: 'Priya Patel', email: 'priya.patel@outlook.com',
    phone: '+91 87654 32109', college: 'NIT Surat', cgpa: '8.7',
    role: 'Backend Developer', status: 'offer',
    appliedDate: '2026-06-08', interviewDate: '2026-07-18',
    salary: '₹22,000/month', joiningDate: '2024-02-05',
    skills: ['Python', 'FastAPI', 'PostgreSQL'],
    resumeScore: 88, avatar: null,
    address: '45, Ring Road, Surat, Gujarat',
    bank: null, pan: null, aadhaar: null,
  },
  {
    id: '3', name: 'Arjun Verma', email: 'arjun.v@yahoo.com',
    phone: '+91 76543 21098', college: 'VIT Vellore', cgpa: '8.5',
    role: 'Full Stack Developer', status: 'hired',
    appliedDate: '2026-06-10', interviewDate: '2026-07-20',
    salary: '₹20,000/month', joiningDate: '2024-02-10',
    skills: ['Node.js', 'React', 'MongoDB'],
    resumeScore: 85, avatar: null,
    address: '7, Anna Salai, Chennai, Tamil Nadu',
    bank: 'SBI - XXXX5678', pan: 'FGHIJ5678K', aadhaar: 'XXXX XXXX 9012',
  },
  {
    id: '4', name: 'Sneha Iyer', email: 'sneha.iyer@gmail.com',
    phone: '+91 65432 10987', college: 'BITS Pilani', cgpa: '9.0',
    role: 'UI/UX Designer', status: 'accepted',
    appliedDate: '2026-06-12', interviewDate: '2026-07-22',
    salary: null, joiningDate: null,
    skills: ['Figma', 'Adobe XD', 'Prototyping'],
    resumeScore: 91, avatar: null, address: null, bank: null, pan: null, aadhaar: null,
  },
  {
    id: '5', name: 'Karan Mehta', email: 'karan.mehta@gmail.com',
    phone: '+91 54321 09876', college: 'DTU Delhi', cgpa: '7.9',
    role: 'Data Analyst', status: 'interview',
    appliedDate: '2026-06-14', interviewDate: '2026-07-14',
    salary: null, joiningDate: null,
    skills: ['Python', 'Pandas', 'SQL', 'PowerBI'],
    resumeScore: 79, avatar: null, address: null, bank: null, pan: null, aadhaar: null,
  },
  {
    id: '6', name: 'Ananya Singh', email: 'ananya.s@gmail.com',
    phone: '+91 43210 98765', college: 'SRM Chennai', cgpa: '8.3',
    role: 'DevOps Engineer', status: 'shortlisted',
    appliedDate: '2026-06-16', interviewDate: null,
    salary: null, joiningDate: null,
    skills: ['Docker', 'Kubernetes', 'AWS'],
    resumeScore: 83, avatar: null, address: null, bank: null, pan: null, aadhaar: null,
  },
  {
    id: '7', name: 'Vikram Reddy', email: 'vikram.r@gmail.com',
    phone: '+91 32109 87654', college: 'Manipal MIT', cgpa: '7.5',
    role: 'Mobile Developer', status: 'applied',
    appliedDate: '2026-06-18', interviewDate: null,
    salary: null, joiningDate: null,
    skills: ['Flutter', 'Dart', 'Firebase'],
    resumeScore: 75, avatar: null, address: null, bank: null, pan: null, aadhaar: null,
  },
  {
    id: '8', name: 'Divya Nair', email: 'divya.nair@gmail.com',
    phone: '+91 21098 76543', college: 'Amity University', cgpa: '8.1',
    role: 'ML Engineer', status: 'rejected',
    appliedDate: '2026-06-05', interviewDate: '2026-07-12',
    salary: null, joiningDate: null,
    skills: ['TensorFlow', 'PyTorch', 'Python'],
    resumeScore: 80, avatar: null, address: null, bank: null, pan: null, aadhaar: null,
  },
  {
    id: '9', name: 'Rohan Gupta', email: 'rohan.g@outlook.com',
    phone: '+91 10987 65432', college: 'IIT Delhi', cgpa: '9.5',
    role: 'Cloud Engineer', status: 'shortlisted',
    appliedDate: '2026-06-20', interviewDate: null,
    salary: null, joiningDate: null,
    skills: ['GCP', 'Terraform', 'Python'],
    resumeScore: 95, avatar: null, address: null, bank: null, pan: null, aadhaar: null,
  },
  {
    id: '10', name: 'Meera Joshi', email: 'meera.j@gmail.com',
    phone: '+91 99887 76655', college: 'COEP Pune', cgpa: '8.6',
    role: 'Backend Developer', status: 'interview',
    appliedDate: '2026-06-22', interviewDate: '2026-07-16',
    salary: null, joiningDate: null,
    skills: ['Java', 'Spring Boot', 'MySQL'],
    resumeScore: 86, avatar: null, address: null, bank: null, pan: null, aadhaar: null,
  },
]

// ─── Mock Interviews ──────────────────────────────────────────────────────────
export const mockInterviews = [
  {
    id: 'i1', candidateId: '5', candidateName: 'Karan Mehta',
    college: 'DTU Delhi', role: 'Data Analyst',
    interviewer: 'Rakesh Kumar', date: '2026-07-14', time: '10:00 AM',
    meetLink: 'https://meet.google.com/abc-defg-hij',
    status: 'scheduled', notes: 'Focus on SQL and Python proficiency'
  },
  {
    id: 'i2', candidateId: '10', candidateName: 'Meera Joshi',
    college: 'COEP Pune', role: 'Backend Developer',
    interviewer: 'Sunita Rao', date: '2026-07-16', time: '02:00 PM',
    meetLink: 'https://meet.google.com/xyz-uvwx-yz',
    status: 'scheduled', notes: 'Check Spring Boot knowledge'
  },
  {
    id: 'i3', candidateId: '4', candidateName: 'Sneha Iyer',
    college: 'BITS Pilani', role: 'UI/UX Designer',
    interviewer: 'Pradeep Singh', date: '2026-07-22', time: '11:30 AM',
    meetLink: 'https://meet.google.com/lmn-opqr-st',
    status: 'completed', notes: 'Excellent portfolio'
  },
]

// ─── Mock Activities ──────────────────────────────────────────────────────────
export const mockActivities = [
  { id: 'a1', time: '10:45 AM', type: 'certificate', message: 'Completion email sent to Rahul Sharma', icon: '🏁' },
  { id: 'a2', time: '10:20 AM', type: 'certificate', message: 'Certificate generated for Rahul Sharma', icon: '🎓' },
  { id: 'a3', time: '09:55 AM', type: 'offer', message: 'Offer letter sent to Priya Patel', icon: '✉️' },
  { id: 'a4', time: '09:45 AM', type: 'offer', message: 'Offer PDF generated for Priya Patel', icon: '📄' },
  { id: 'a5', time: '09:30 AM', type: 'interview', message: 'Interview invite sent to Karan Mehta', icon: '📧' },
  { id: 'a6', time: '09:15 AM', type: 'hired', message: 'Arjun Verma marked as Hired', icon: '✅' },
  { id: 'a7', time: '08:50 AM', type: 'shortlist', message: 'Ananya Singh shortlisted', icon: '⭐' },
  { id: 'a8', time: '08:30 AM', type: 'shortlist', message: 'Rohan Gupta shortlisted', icon: '⭐' },
]

// ─── Mock Dashboard Stats ─────────────────────────────────────────────────────
export const mockDashboardStats = {
  totalCandidates: 152,
  newApplications: 18,
  shortlisted: 42,
  interviewScheduled: 12,
  interviewAccepted: 8,
  hired: 24,
  offerSent: 6,
  completed: 38,
  todayInterviews: [
    { name: 'Karan Mehta', time: '10:00 AM', role: 'Data Analyst' },
    { name: 'Meera Joshi', time: '02:00 PM', role: 'Backend Developer' },
  ],
  recentActivities: mockActivities.slice(0, 5),
  pendingActions: [
    { id: 1, type: 'offer', message: 'Generate offer for Priya Patel', urgent: true },
    { id: 2, type: 'docs', message: 'Docs pending from Arjun Verma', urgent: false },
    { id: 3, type: 'cert', message: 'Certificate ready for Rahul Sharma', urgent: false },
  ],
}

// ─── Mock Reports Data ────────────────────────────────────────────────────────
export const mockReportsData = {
  monthly: [
    { month: 'Aug', applications: 20, hired: 5, offers: 4 },
    { month: 'Sep', applications: 35, hired: 8, offers: 7 },
    { month: 'Oct', applications: 28, hired: 6, offers: 5 },
    { month: 'Nov', applications: 42, hired: 10, offers: 9 },
    { month: 'Dec', applications: 31, hired: 7, offers: 6 },
    { month: 'Jan', applications: 52, hired: 12, offers: 11 },
  ],
  colleges: [
    { name: 'IIT Bombay', count: 28 },
    { name: 'NIT Surat', count: 21 },
    { name: 'VIT Vellore', count: 18 },
    { name: 'BITS Pilani', count: 16 },
    { name: 'DTU Delhi', count: 14 },
    { name: 'Others', count: 55 },
  ],
  pipeline: [
    { name: 'Applied', value: 152, fill: '#94a3b8' },
    { name: 'Shortlisted', value: 42, fill: '#60a5fa' },
    { name: 'Interviewed', value: 28, fill: '#c084fc' },
    { name: 'Hired', value: 24, fill: '#4ade80' },
    { name: 'Completed', value: 38, fill: '#818cf8' },
  ],
}
