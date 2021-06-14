function search(fragment, minSigns, maxSigns) {
    function escapeRegex(string) {
        return string.replace(/[-\/\\^$*+?.()|[\]{}]/g, "\\$&");
    }
    function create_sign_regexp(sign) {
        return sign === "*" ? "[^\\s]+" : "([X ])*([^\\s]+\\/)*" + escapeRegex(sign) + "(\\/[^\\s]+)*([X ])*"
    }
    function create_line_regexp(line) {
        return line.map(create_sign_regexp).join(" ")
    }
    function create_regexp(signs) {
        return signs.map(create_line_regexp).join("( .*)?\\n.*")
    }
    const signs = fragment.signs.replace(/X/g, "").replace(/ +/g, " ")
    const signMatrix = signs.split("\n").map(line => line.trim().split(" ").filter(sign => sign !== "")).filter(line => line.length > 0)
    const numSigns = signMatrix.reduce((acc, line) => acc.concat(line), []).length
    if (numSigns < minSigns || numSigns > maxSigns) {
        return {
            _id: fragment._id,
            notes: fragment.notes
        }
    }
    let result = {}
    signMatrix.forEach((line, y) => {
      line.forEach((sign, x) => {
        const wildcarded = JSON.parse(JSON.stringify(signMatrix))
        wildcarded[y][x] = "*"
        result = db.getCollection("chapters").find(
          {signs: new RegExp(create_regexp(wildcarded))}, 
          {_id: 1, textId: 1, stage: 1, name: 1}
        ).toArray().reduce((acc, match) => {            
            const stringId = String(match._id)
            if(!acc[stringId]) {
                acc[stringId] = {
                    numberOfMatches: 1,
                    _id: match._id,
                    textId: match.textId,
                    textName: db.getCollection("texts").findOne(match.textId).name,
                    chapterName: match.name,
                }
            } else {
                acc[stringId].numberOfMatches++
            }
            return acc
        }, result)
      })  
    })
    const matches = Object.values(result)
    return {
        _id: fragment._id,
        matches: matches,
        numberOfSigns: numSigns,
        maxMatchPercent: matches.reduce((max,match) => match.numberOfMatches > max ? match.numberOfMatches : max, 0) / numSigns,
        longestRepeat: signs.replace(/[\s\n]+/g, " ").trim().split(" ").reduce((acc, sign) => {
            return acc.lastSign === sign ? {
                longest: acc.longest <= acc.current ? acc.current + 1 : acc.longest,
                current: acc.current + 1,
                lastSign: sign
            } : {
                longest: acc.longest,
                current: 1,
                lastSign: sign
            }
        }, {longest: 1, current: 0, lastSign: ""}).longest,
        notes: fragment.notes
    }
}

const skip = 0
const limit = 10
const minSigns = 1
const maxSigns = 100

printjson(
    db.getCollection("fragments")
    .find({signs: {$ne: "", $exists: true}}, {_id: 1, notes: 1, signs: 1})
    .addOption(DBQuery.Option.noTimeout)
    .sort( { _id: 1 } )
    .skip(skip).limit(limit)
    .map(fragment => search(fragment, minSigns, maxSigns))
    .filter(match => match.matches !== undefined && match.matches.length > 0)
    .sort((a, b) => a.maxMatchPercent === b.maxMatchPercent ? a.longestRepeat - b.longestRepeat : b.maxMatchPercent - a.maxMatchPercent)
)
