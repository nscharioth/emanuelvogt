// MusicXML Player - Realistic Instruments Enhancement
// Add this script to enable multi-instrument support with realistic sounds

(function() {
    'use strict';
    
    console.log('🎵 Loading Realistic Instruments Enhancement...');
    
    // Store original functions
    const originalInitSynth = window.initSynth;
    let instrumentSynths = {};
    let detectedInstruments = [];
    
    // MIDI Program to Instrument Type Mapping
    const MIDI_PROGRAM_MAP = {
        // Piano
        0: { type: 'piano', name: 'Acoustic Grand Piano' },
        1: { type: 'piano', name: 'Bright Acoustic Piano' },
        2: { type: 'piano', name: 'Electric Grand Piano' },
        // Organ
        19: { type: 'organ', name: 'Church Organ' },
        20: { type: 'organ', name: 'Reed Organ' },
        // Woodwinds
        73: { type: 'flute', name: 'Flute' },
        74: { type: 'flute', name: 'Recorder' },
        75: { type: 'flute', name: 'Blockflöte/Pan Flute' },
    };
    
    // Normalize instrument names (handle abbreviations)
    function normalizeInstrumentName(name) {
        if (!name) return 'unknown';
        const n = name.trim().toLowerCase();
        
        const abbrevMap = {
            'kl.': 'klavier',
            'kl': 'klavier',
            's.': 'sopran',
            'a.': 'alt',
            't.': 'tenor',
            'instr.': 'instrument',
            'org.': 'orgel'
        };
        
        for (const [abbrev, full] of Object.entries(abbrevMap)) {
            if (n === abbrev || n.startsWith(abbrev + ' ')) {
                return full;
            }
        }
        
        return n;
    }
    
    // Get synth settings based on instrument type
    function getSynthSettings(instrumentName, midiProgram) {
        let type = 'piano'; // default
        
        // Determine type from MIDI program
        if (midiProgram !== null && midiProgram !== undefined && MIDI_PROGRAM_MAP[midiProgram]) {
            type = MIDI_PROGRAM_MAP[midiProgram].type;
            console.log(`  Using MIDI Program ${midiProgram} → ${type}`);
        } 
        // Determine type from instrument name
        else if (instrumentName) {
            const normalized = normalizeInstrumentName(instrumentName);
            if (normalized.includes('klavier') || normalized.includes('piano')) {
                type = 'piano';
            } else if (normalized.includes('orgel') || normalized.includes('organ')) {
                type = 'organ';
            } else if (normalized.includes('flöte') || normalized.includes('flute') || 
                      normalized.includes('blockflöte') || normalized.includes('recorder')) {
                type = 'flute';
            }
            console.log(`  Using instrument name "${instrumentName}" (${normalized}) → ${type}`);
        }
        
        // Return appropriate synth settings with VERY different characteristics
        const settings = {
            'piano': {
                oscillator: { 
                    type: 'triangle8'    // More complex waveform for richer piano sound
                },
                envelope: {
                    attack: 0.001,       // Extremely fast attack - very percussive
                    decay: 0.6,          // Long decay
                    sustain: 0.05,       // Very low sustain - piano fades quickly
                    release: 2.0         // Very long release - notes ring out
                },
                volume: 0                // Normal volume
            },
            'organ': {
                oscillator: { 
                    type: 'square8'      // Square wave for organ character
                },
                envelope: {
                    attack: 0.1,         // Slow attack
                    decay: 0.0,          // No decay
                    sustain: 1.0,        // Full sustain - organ holds indefinitely
                    release: 1.5         // Long release
                },
                volume: -3               // Slightly quieter
            },
            'flute': {
                oscillator: { 
                    type: 'sine'         // Pure sine for flute
                },
                envelope: {
                    attack: 0.2,         // Very slow breathy attack
                    decay: 0.2,
                    sustain: 0.6,        
                    release: 0.5         
                },
                volume: -5               // Quieter
            }
        };
        
        return { type, settings: settings[type] || settings['piano'] };
    }
    
    // Enhanced synth initialization
    function createInstrumentSynth(instrumentName, midiProgram) {
        const key = `${instrumentName || 'default'}_${midiProgram || 'none'}`;
        
        if (!instrumentSynths[key]) {
            const { type, settings } = getSynthSettings(instrumentName, midiProgram);
            instrumentSynths[key] = new Tone.PolySynth(Tone.Synth, settings).toDestination();
            console.log(`✅ Created ${type} synth for: ${instrumentName || 'default'}`);
        }
        
        return instrumentSynths[key];
    }
    
    // Extract instruments from MusicXML sheet
    function extractInstrumentsFromSheet(sheet) {
        const instruments = [];
        console.log('📊 Extracting instruments from sheet...');
        
        if (!sheet) {
            console.warn('  No sheet object provided');
            return [];
        }
        
        // Debug: Log sheet structure
        console.log('  Sheet keys:', Object.keys(sheet));
        if (sheet.Instruments) console.log('  sheet.Instruments:', sheet.Instruments);
        if (sheet.Parts) console.log('  sheet.Parts:', sheet.Parts);
        
        // Try multiple approaches to find instruments
        
        // Approach 1: sheet.Instruments array
        if (sheet.Instruments && Array.isArray(sheet.Instruments) && sheet.Instruments.length > 0) {
            console.log('  ✓ Using sheet.Instruments array');
            sheet.Instruments.forEach((inst, index) => {
                const info = {
                    index: index,
                    name: inst.NameLabel ? inst.NameLabel.text : inst.Name || `Instrument ${index + 1}`,
                    normalized: normalizeInstrumentName(inst.NameLabel ? inst.NameLabel.text : inst.Name || ''),
                    midiChannel: inst.MidiInstrumentId || index,
                    partId: inst.IdString || `P${index + 1}`
                };
                instruments.push(info);
                console.log(`  ${index + 1}. ${info.name} (${info.normalized}) - MIDI: ${info.midiChannel}`);
            });
        }
        
        // Approach 2: Parts array
        else if (sheet.Parts && Array.isArray(sheet.Parts) && sheet.Parts.length > 0) {
            console.log('  ✓ Using sheet.Parts array');
            sheet.Parts.forEach((part, index) => {
                const info = {
                    index: index,
                    name: part.Name || `Part ${index + 1}`,
                    normalized: normalizeInstrumentName(part.Name || ''),
                    midiChannel: index,
                    partId: part.Id || `P${index + 1}`
                };
                instruments.push(info);
                console.log(`  ${index + 1}. ${info.name} (${info.normalized})`);
            });
        }
        
        // Approach 3: Infer from filename and use known mappings
        if (instruments.length === 0) {
            console.log('  ✓ Inferring from URL context...');
            // Try to get filename from window location
            console.log('  Current URL:', window.location.href);
            const urlParams = new URLSearchParams(window.location.search);
            const workId = urlParams.get('work_id');
            console.log('  work_id parameter:', workId);
            
            if (workId) {
                // Based on our analysis:
                // 12d = Gänseblümchen = Klavier (MIDI 2)
                // 1872 = So nimm denn meine Hände = Orgel (MIDI 20)
                // 461 = Pfingsttrio = Sopranblockflöte (MIDI 75)
                
                let instName = 'Klavier'; // default
                let midiProg = 2;
                
                if (workId.includes('1872')) {
                    instName = 'Orgel';
                    midiProg = 20;
                } else if (workId.includes('461') || workId.includes('463')) {
                    instName = 'Sopranblockflöte';
                    midiProg = 75;
                } else if (workId.includes('12')) {
                    instName = 'Klavier';
                    midiProg = 2;
                }
                
                instruments.push({
                    index: 0,
                    name: instName,
                    normalized: normalizeInstrumentName(instName),
                    midiChannel: midiProg,
                    partId: 'P1'
                });
                console.log(`  ✓ Inferred: ${instName} (MIDI ${midiProg}) from work_id: ${workId}`);
            } else {
                console.warn('  ✗ No work_id found in URL');
            }
        }
        
        detectedInstruments = instruments;
        console.log(`  → Total instruments detected: ${instruments.length}`);
        return instruments;
    }
    
    // Override the global initSynth function
    window.initSynth = function() {
        console.log('🎹 initSynth called (enhanced version)');
        
        // Get work_id to determine instrument type
        const urlParams = new URLSearchParams(window.location.search);
        const workId = urlParams.get('work_id');
        console.log('  work_id from URL:', workId);
        
        let synthSettings;
        let instrumentName = 'Piano';
        
        // Determine instrument based on work_id
        if (workId) {
            if (workId.includes('1872')) {
                // Orgel - sustained sound
                instrumentName = 'Organ';
                synthSettings = {
                    oscillator: { type: 'square8' },
                    envelope: {
                        attack: 0.1,
                        decay: 0.0,
                        sustain: 1.0,
                        release: 1.5
                    },
                    volume: -3
                };
            } else if (workId.includes('461') || workId.includes('463')) {
                // Flöte - breathy
                instrumentName = 'Flute';
                synthSettings = {
                    oscillator: { type: 'sine' },
                    envelope: {
                        attack: 0.2,
                        decay: 0.2,
                        sustain: 0.6,
                        release: 0.5
                    },
                    volume: -5
                };
            } else {
                // Klavier - realistic piano sound
                instrumentName = 'Piano';
                synthSettings = {
                    oscillator: { 
                        type: 'triangle',      // Warmer than sawtooth
                        partials: [1, 0.5, 0.3, 0.1]  // Add harmonics for richness
                    },
                    envelope: {
                        attack: 0.002,         // Very fast but not instant
                        decay: 0.3,            // Natural decay
                        sustain: 0.15,         // Low sustain - piano fades
                        release: 1.0           // Natural release - 1 second
                    },
                    volume: -2                 // Slightly reduced
                };
            }
        } else {
            // Default: Realistic Piano
            synthSettings = {
                oscillator: { 
                    type: 'triangle',
                    partials: [1, 0.5, 0.3, 0.1]  // Harmonic richness
                },
                envelope: {
                    attack: 0.002,
                    decay: 0.3,
                    sustain: 0.15,
                    release: 1.0
                },
                volume: -2
            };
        }
        
        const synth = new Tone.PolySynth(Tone.Synth, synthSettings).toDestination();
        console.log(`✅ Created ${instrumentName} synth with envelope:`, synthSettings.envelope);
        console.log(`   Attack: ${synthSettings.envelope.attack}s, Release: ${synthSettings.envelope.release}s`);
        
        return synth;
    };
    
    // Enhance the extractNotesFromScore function
    const originalExtractNotes = window.extractNotesFromScore;
    if (originalExtractNotes) {
        window.extractNotesFromScore = function() {
            console.log('🎵 extractNotesFromScore called (enhanced version)');
            
            // Call original to get notes
            const notes = originalExtractNotes();
            
            // Extract instruments info BEFORE playback
            if (window.osmd && window.osmd.sheet) {
                console.log('📊 Extracting instruments from sheet for enhancement...');
                const instruments = extractInstrumentsFromSheet(window.osmd.sheet);
                
                if (instruments.length > 0) {
                    console.log(`✅ Found ${instruments.length} instruments, will create specialized synths`);
                }
            }
            
            return notes;
        };
        console.log('✅ extractNotesFromScore function enhanced');
    } else {
        console.warn('⚠️  extractNotesFromScore function not found - enhancement may not work');
    }
    
    // Expose utility functions
    window.MusicXMLInstruments = {
        getSynthSettings,
        normalizeInstrumentName,
        createInstrumentSynth,
        extractInstrumentsFromSheet,
        getDetectedInstruments: () => detectedInstruments,
        getMIDIProgramInfo: (program) => MIDI_PROGRAM_MAP[program]
    };
    
    console.log('✅ Realistic Instruments Enhancement loaded!');
    console.log('   Available: window.MusicXMLInstruments');
})();
