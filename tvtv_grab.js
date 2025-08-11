const fs = require('fs');
const axios = require('axios');
const { Builder } = require('xml2js');
const moment = require('moment');

// Configuration
const channels = [
    {
        "site_id": "33453",
        "channel_name": "PBS HD",
        "channel_id": "33453"
    }
    // Add more channels as needed
];
const outputFile = 'guide.xml';
const daysToFetch = 1; // Number of days to fetch

// XMLTV Generator
async function generateXmltv() {
    const xmlBuilder = new Builder({
        headless: true,
        renderOpts: { pretty: true, indent: '  ', newline: '\n' }
    });

    const xmltv = {
        tv: {
            $: {
                'source-info-url': 'https://www.tvtv.us',
                'source-info-name': 'TVTV.us',
                'generator-info-name': 'tvtv-us-xmltv',
                'generator-info-url': ''
            },
            channel: [],
            programme: []
        }
    };

    // Add channels
    for (const channel of channels) {
        xmltv.tv.channel.push({
            $: { id: channel.channel_id },
            'display-name': [{ _: channel.channel_name, $: { lang: 'en' } }]
        });
    }

    // Fetch program data for each channel
    for (const channel of channels) {
        for (let i = 0; i < daysToFetch; i++) {
            const date = moment().add(i, 'days');
            const startTime = date.clone().startOf('day').add(4, 'hours'); // 04:00 UTC
            const endTime = date.clone().add(1, 'days').startOf('day').add(3, 'hours').add(59, 'minutes').add(59, 'seconds'); // 03:59:59 UTC next day

            try {
                const url = `https://cors-anywhere.com/https://www.tvtv.us/api/v1/lineup/USA-GNSTR-X/grid/${startTime.toISOString()}/${endTime.toISOString()}/${channel.site_id}`;
                const response = await axios.get(url);
                const programs = response.data;

                for (const program of programs) {
                    // Fetch additional program details
                    let programDetails = {};
                    try {
                        const detailsUrl = `https://cors-anywhere.com/https://tvtv.us/api/v1/programs/${program.programId}`;
                        const detailsResponse = await axios.get(detailsUrl);
                        programDetails = detailsResponse.data;
                    } catch (error) {
                        console.error(`Error fetching details for program ${program.programId}:`, error.message);
                    }

                    // Create programme entry
                    const start = moment(program.startTime).format('YYYYMMDDHHmmss ZZ');
                    const stop = moment(program.endTime).format('YYYYMMDDHHmmss ZZ');

                    const programme = {
                        $: {
                            start: start,
                            stop: stop,
                            channel: channel.channel_id
                        },
                        title: [{ _: program.title, $: { lang: 'en' } }],
                        'sub-title': program.subtitle ? [{ _: program.subtitle, $: { lang: 'en' } }] : [],
                        desc: programDetails.description ? [{ _: programDetails.description, $: { lang: 'en' } }] : [],
                        category: program.genres ? program.genres.map(genre => ({ _: genre, $: { lang: 'en' } })) : [],
                        'episode-num': program.episodeTitle ? [
                            { _: program.episodeTitle, $: { system: 'onscreen' } }
                        ] : []
                    };

                    if (programDetails.originalAirDate) {
                        programme.date = moment(programDetails.originalAirDate).format('YYYY');
                    }

                    xmltv.tv.programme.push(programme);
                }
            } catch (error) {
                console.error(`Error fetching data for channel ${channel.channel_id} on ${date.format('YYYY-MM-DD')}:`, error.message);
            }
        }
    }

    // Generate XML
    const xml = xmlBuilder.buildObject(xmltv);

    // Write to file
    fs.writeFileSync(outputFile, xml);
    console.log(`XMLTV guide saved to ${outputFile}`);
}

generateXmltv().catch(console.error);