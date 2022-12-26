//Total number of BRs and MRs
// Longest MR
// Shortest MR
// Most popular MR/BR (highest number of participants)
// Top genres (MR/BR)
// Top 5 readers (most MRs/BRs participated in)
// Total pages read as a server (combined MRs/BRs) 
// Top 3(?) BR leaders

const fs = require('fs').promises

async function readEventList(path) {
    const data = await fs.readFile(path, 'utf8');
    return JSON.parse(data);
}

function isApprovedEvent(event) {
    if(event.read_by.length > 0)
        return true;
    else
        return false;
}
function isBuddyRead(event) {
    return event.type === "BR"
}

function isMonthlyRead(event) {
    return event.type === "MR"
}

function getPageNum(event) {
    let num_pages = parseInt(event.book.num_pages.split(' ')[0]);
    if(!num_pages)
        return 0;
    else
        return num_pages;
}

function getReaderNum(event) {
    let num_readers = parseInt(event.read_by.length);
    if(!num_readers)
        return 0;
    else
        return num_readers;
}

function getReactorNum(event) {
    let num_reactors = parseInt(event.announce_reactors.length);
    if(!num_reactors)
        return 0;
    else
        return num_reactors;
}

function comparePageCount(x, y) {
    let pageX = getPageNum(x); 
    let pageY = getPageNum(y);
    if(pageX < pageY)
        return -1;
    else if(pageX > pageY)
        return 1;
    else
        return 0;
}

function compareReaderCount(x, y) {
    let readersX = getReaderNum(x); 
    let readersY = getReaderNum(y);
    if(readersX < readersY)
        return -1;
    else if(readersX > readersY)
        return 1;
    else
        return 0;
}

function compareReactorCount(x, y) {
    let reactorsX = getReactorNum(x); 
    let reactorsY = getReactorNum(y);
    if(reactorsX < reactorsY)
        return -1;
    else if(reactorsX > reactorsY)
        return 1;
    else
        return 0;
}
function getPageStats(events, eventType) {
    events.sort(comparePageCount);
    const shortest = events[0];
    console.log(`Shortest ${eventType}: ${shortest.book.title} with ${shortest.book.num_pages}`);
    const longest = events[events.length - 1];
    console.log(`Longest ${eventType}: ${longest.book.title} with ${longest.book.num_pages}`);
    let res = 0;
    events.forEach(event => {
        res += getPageNum(event);
    });
    console.log(`Total pages read: ${res} pages`);
    console.log("");
}

function getReactorStats(events, eventType) {
    events.sort(compareReactorCount);
    const leastPopular = events[0];
    console.log(`Least Reacted ${eventType}: ${leastPopular.book.title} with ${leastPopular.announce_reactors.length} reactors`);
    const mostPopular = events[events.length - 1];
    console.log(`Most Reacted ${eventType}: ${mostPopular.book.title} with ${mostPopular.announce_reactors.length} reactors`);
    console.log("");
}

function getParticipantStats(events, eventType) {
    events.sort(compareReaderCount);
    const leastPopular = events[0];
    console.log(`Least Popular ${eventType}: ${leastPopular.book.title} with ${leastPopular.read_by.length} participants`);
    const mostPopular = events[events.length - 1];
    console.log(`Most Popular ${eventType}: ${mostPopular.book.title} with ${mostPopular.read_by.length} participants`);
    console.log("");
}

function getGenreStats(events, eventType) {
    let genreDict = {};
    events.forEach(event => {
        event.book.genres.forEach(genre => {
            if(!genreDict[genre])
                genreDict[genre] = 1;
            else
                genreDict[genre] += 1;
        });
    });
    let genreArray = [];
    for(var genre in genreDict)
    {
        genreArray.push([genreDict[genre], genre]);
    }
    genreArray.sort((x, y) => {
        return y[0] - x[0];
    });
    console.log(`Top 5 Genres for ${eventType}s are: `)
    for(var i=0;i<5;i++)
    {
        console.log(`${i+1}) ${genreArray[i][1]}`);
    }
    console.log("");
}

function getReaderStats(events, eventType) {
    let userDict = {};
    events.forEach(event => {
        event.read_by.forEach(user => {
            if(!userDict[user.toString()])
                userDict[user.toString()] = 1;
            else
                userDict[user.toString()] += 1;
        });
    });
    let userArray = [];
    for(var user in userDict)
    {
        userArray.push([userDict[user], user]);
    }
    userArray.sort((x, y) => {
        return y[0] - x[0];
    });
    console.log(`Top 5 Readers for ${eventType}s are: `)
    for(var i=0;i<5;i++)
    {
        console.log(`${i+1}) ${userArray[i][1]} with ${userArray[i][0]} ${eventType}s`);
    }
    console.log("");
}

function getLeaderStats(events, eventType) {
    let userDict = {};
    events.forEach(event => {
        event.requested_by.forEach(user => {
            if(!userDict[user.toString()])
                userDict[user.toString()] = 1;
            else
                userDict[user.toString()] += 1;
        });
    });
    let userArray = [];
    for(var user in userDict)
    {
        userArray.push([userDict[user], user]);
    }
    userArray.sort((x, y) => {
        return y[0] - x[0];
    });
    console.log(`Top 5 Leaders for ${eventType}s are: `)
    for(var i=0;i<5;i++)
    {
        console.log(`${i+1}) ${userArray[i][1]} with ${userArray[i][0]} ${eventType}s`);
    }
    console.log("");
}

(async () => {
    var eventList = await readEventList("./stats.json");
    var approvedEvents = eventList.filter(isApprovedEvent);
    
    var approvedBRs = approvedEvents.filter(isBuddyRead);
    console.log(`Total BRs: ${approvedBRs.length}`);
    
    var approvedMRs = approvedEvents.filter(isMonthlyRead);
    console.log(`Total MRs: ${approvedMRs.length}`);
    console.log("");
    
    getPageStats(approvedBRs, "BR");
    getPageStats(approvedMRs, "MR");
    
    getReactorStats(approvedBRs, "BR");
    getReactorStats(approvedMRs, "MR");
    
    getParticipantStats(approvedBRs, "BR");
    getParticipantStats(approvedMRs, "MR");
    
    getGenreStats(approvedBRs, "BR");
    getGenreStats(approvedMRs, "MR");
    
    getReaderStats(approvedBRs, "BR");
    getReaderStats(approvedMRs, "MR");

    getLeaderStats(approvedBRs, "BR");

})();
